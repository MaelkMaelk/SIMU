
# Native import
import time
from pathlib import Path
import os

# fichiers
from Python.network import Network
import Python.server_browser as server_browser
from Python.player import *
import Python.interface as interface
from Python.paquets_avion import *
import Python.outils_radar as outils_radar
import Python.capture as capture
import Python.carte_defs as carte_defs
import Python.fdw as fdw
import Python.outils_creation as outils_creation

# recherche de tous les serveurs sur le réseau
address = server_browser.serverBrowser()
if address:
    print(address)
else:
    time.sleep(20)
    exit()

# fenêtre Pygame, mettre en 1920, 1080 pour plein écran
pygame.init()
width = 1000
height = 1000
win = pygame.display.set_mode((width, height))

# win = pygame.display.set_mode()
# width, height = pygame.display.get_surface().get_size()

path = Path(os.getcwd())
manager = pygame_gui.UIManager((width, height), path / 'ressources' / 'theme.json')

pygame.display.set_caption("Client")
temps = pygame.time.get_ticks()
clock = pygame.time.Clock()
font = pygame.font.SysFont('arial', 16, bold=True)

if replayMode:
    dossierScreen = Path('replay') / (str(time.localtime()[1]) + '_' + str(time.localtime()[2]) + '_' +
                                      str(time.localtime()[3]) + 'h' + str(time.localtime()[4]))
    dossierScreen.mkdir()


def main(server_ip: str):
    global temps
    global height
    global width
    run = True

    distance = 10
    # menus
    conflitBool = False
    conflitGen = None
    menuATC = None
    menuValeurs = None
    flightDataWindow = None
    menuRadar = interface.menuRadar()
    menuRadarTimer = 0
    save_text_timing = - temps_affichage_text - 1

    # screenshots replays
    dernierScreen = pygame.time.get_ticks()

    # on se connecte au serveur
    n = Network(server_ip)
    packet = n.getP()

    i = 0
    packetId = 0
    while packet is None and i < 200:
        n = Network(server_ip)
        packet = n.getP()
        time.sleep(0.3)
        i +=1

    perfos = packet.perfos
    game = packet.game
    dictAvionsAff = {}
    dictAvions = packet.dictAvions
    dict_avion_spawn = packet.listeTotale

    # Map
    carte = packet.map
    mapScale = carte['mapScale']

    # alidad
    alidad = False
    alidadPos = (0, 0)
    curseur_alidad = False

    # cercles
    curseur_cercles = False
    cerclePos = None

    # alisep
    curseur_aliSep = False
    sepDict = {'A': outils_radar.aliSep('A'), 'B': outils_radar.aliSep('B'), 'C': outils_radar.aliSep('C')}

    # scroll and zoom
    zoomDef = 0.5
    scrollDef: list[float] = [width / 4, height/4]
    zoom = zoomDef
    scroll = scrollDef
    drag = [0, 0]
    mouseDownTime = 0
    empecherDragging = False

    # vecteurs et type
    vecteurs = False
    vecteurSetting = 6

    # fenêtre nouvel avion
    nouvelAvionWin = None

    # fenêtre modifs
    modifWindow = None

    # pour qu'on n'ait qu'un seul appui par touche
    pressing = False
    delaiPressage = pygame.time.get_ticks()

    # pilote
    pilote = False

    while run:
        localRequests = []
        tempoPacket = packet

        time_delta = clock.tick(60) / 1000.0
        clock.tick(60)

        for avionId, avion in packet.dictAvions.items():  # on parcourt le paquet qu'on a reçu du serveur

            if avionId in dictAvionsAff.keys():  # si l'avion est deja dans notre liste locale
                # on l'update avec la methode update de la classe avion
                dictAvionsAff[avionId].update(avion)
            else:  # sinon
                # on l'ajoute avec methode update de la classe dict
                dictAvionsAff.update({avionId: Avion(avionId, avion, zoom, scroll)})

        if len(dictAvionsAff) > len(packet.dictAvions):  # si on a plus d'avions locaux qu'on en reçoit
            toBeRemovedOther = []
            for avionId in dictAvionsAff.keys():  # on itère sur la boucle locale
                # si on trouve un avion local qui n'est pas dans les données reçues
                if avionId not in list(packet.dictAvions.keys()):
                    toBeRemovedOther.append(avionId)
            for avionId in toBeRemovedOther:
                # 2em boucle pour supprimer, car on ne peut pas delete en pleine iteration
                dictAvionsAff[avionId].kill()
                dictAvionsAff.pop(avionId)

        carte = packet.map
        game = packet.game
        dictAvions = packet.dictAvions
        if packet.listeTotale is not None:
            dict_avion_spawn = packet.listeTotale

        for sep in sepDict.values():
            sep.calculation(carte)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()

            if event.type == pygame_gui.UI_BUTTON_ON_HOVERED:

                if menuValeurs:  # on regarde ici pour dessiner les directs
                    menuValeurs.checkHovered(event)

                for avion in dictAvionsAff.values():
                    if avion.checkEtiquetteOnHover():  # renvoies True quand le bouton correspond à cette etiquette
                        if flightDataWindow:  # si la FDW est déployée
                            flightDataWindow.linkAvion(avion, carte['points'], game.heure)  # on associe l'avion à la FDW

                        break  # dès qu'on a trouvé le responsable, on casse

            elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED:
                if menuValeurs:
                    menuValeurs.checkUnHovered(event)

            elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
                empecherDragging = True

                for avion in dictAvionsAff.values():
                    if avion.etiquetteExtended:  # si c'est cette etiquette qu'on survole
                        avion.startPressTime = pygame.time.get_ticks()
                        avion.dragOffset = calculateEtiquetteOffset(avion.etiquette.container)

            # on vérifie que l'alidade n'est pas actif
            elif event.type == pygame_gui.UI_BUTTON_PRESSED and curseur_alidad:
                empecherDragging = False

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                empecherDragging = False
                
                if menuRadar.checkActive():
                    action = menuRadar.checkEvent(event)

                    if action is not None:

                        if type(action) in [list, tuple]:

                            if action[0] == 'VecteursToggle':
                                if vecteurSetting == action[1]:
                                    vecteurs = not vecteurs
                                else:
                                    vecteurs = True
                                    vecteurSetting = action[1]

                            elif action[0] == 'Vecteurs':
                                vecteurSetting = action[1]

                            elif action[0] == 'Sep':
                                sepDict[action[1]].kill()
                                curseur_aliSep = action[1]
                                pygame.mouse.set_cursor(pygame.cursors.diamond)
                        elif action == 'Alidade':
                            curseur_alidad = True
                            pygame.mouse.set_cursor(pygame.cursors.broken_x)

                        elif action == 'Cercles':
                            cerclePos = None
                            curseur_cercles = True
                            pygame.mouse.set_cursor(pygame.cursors.broken_x)

                if menuATC is not None:

                    # si on valide les modifs, alors la fonction checkEvent retourne les modifs
                    action = menuATC.checkEvent(event)
                    if action:
                        if type(action) in [list, tuple]:  # si c'est un tuple alors cela correspond à une requête
                            localRequests.append(action)

                if conflitGen is not None:
                    action = conflitGen.checkEvent(event)

                    if action:
                        if type(action) is tuple:
                            localRequests.append((len(dictAvions), "DelayedAdd", action))
                        else:
                            localRequests.append((len(dictAvions), "Add", action))
                        for avion in dictAvionsAff.values():
                            avion.conflitSelected = False
                        conflitBool = False
                        conflitGen = None

                if menuValeurs is not None:

                    # si on valide les modifs, alors la fonction checkEvent retourne les modifs
                    action = menuValeurs.checkEvent(event)
                    if action:
                        if type(action) in [list, tuple]:  # si c'est un tuple alors cela correspond à une requête
                            localRequests.append(action)
                        elif type(action) is str:
                            menuValeurs = interface.menuValeurs(menuValeurs.avion, pygame.mouse.get_pos(), action, pilote)

                if curseur_aliSep:
                    for sep in sepDict:
                        if sep == curseur_aliSep:
                            for avion in dictAvionsAff.values():
                                if avion.checkClicked(event):
                                    if sepDict[sep].linkAvion(avion, carte):
                                        curseur_aliSep = False
                                        pygame.mouse.set_cursor(pygame.cursors.arrow)

                else:
                    for avion in dictAvionsAff.values():  # pour chaque avion

                        action = avion.checkEvent(event, pilote, conflitBool)  
                        
                        # on vérifie si l'event est associé avec ses boutons

                        if type(action) in [list, tuple]:  # si c'est un tuple alors cela correspond à une requête
                            localRequests.append(action)

                        elif action == 'menuATC' and menuATC is None:
                            menuATC = interface.menuATC(avion, pygame.mouse.get_pos())

                        elif action == 'modifier':
                            modifWindow = outils_creation.menu_modifs_avion(carte['routes'],
                                                                               perfos,
                                                                               dict_avion_spawn[avion.Id])

                        elif menuValeurs is None and action is not None:
                            # si on a renvoyé autre chose alors c'est une valeur pour ouvrir un menu
                            menuValeurs = interface.menuValeurs(avion, pygame.mouse.get_pos(), action, pilote)

                    # Menu de selection nouvel avion
                    # si notre menu est ouvert
                    if nouvelAvionWin is not None:
                        # si on appuie sur le bouton valider, alors le menu renvoie les valeurs
                        newPlaneData = nouvelAvionWin.checkEvent(event)

                        # on vérifie que newPlane n'est pas None (les valeurs ont été renvoyés
                        if newPlaneData:

                            # on crée alors un nouvel avion
                            FL = None
                            PFL = None
                            if 'FL' in newPlaneData:
                                FL = newPlaneData['FL']
                            if 'PFL' in newPlaneData:
                                PFL = newPlaneData['PFL']

                            newPlane = AvionPacket(
                                carte,
                                len(dictAvions),  # id de l'avion, correspond au dernier avion créé
                                newPlaneData['indicatif'],
                                newPlaneData['avion'],
                                perfos[newPlaneData['avion']],  # on va chercher les perfos complètes
                                carte['routes'][newPlaneData['route']],  # on va chercher la route en entier dans la map
                                newPlaneData['arrival'],
                                game.heure,
                                CPDLC=newPlaneData['CPDLC'],
                                FL=FL,
                                ExRVSM=newPlaneData['ExRVSM'],
                                PFL=PFL)

                            conflitGen = outils_radar.conflictGenerator(win, newPlane, carte)
                            conflitBool = True

                    if modifWindow is not None:
                        modifData = modifWindow.checkEvent(event)

                        if modifData is not None:
                            if 'Remove' in modifData:
                                localRequests.append((modifWindow.avion.Id, 'Remove'))
                            else:
                                localRequests.append((modifWindow.avion.Id, 'Modifier', modifData))

            elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:

                if nouvelAvionWin is not None:
                    nouvelAvionWin.checkFields(event)

                if modifWindow is not None:
                    modifWindow.checkFields(event)

            if nouvelAvionWin or modifWindow:
                pass

            # zoom géré ici
            elif event.type == pygame.MOUSEWHEEL:
                trucScroller = False
                if menuValeurs is not None:
                    trucScroller = menuValeurs.checkScrolled(event)

                if not trucScroller:
                    for avion in dictAvionsAff.values():
                        trucScroller = avion.checkScrolled(event)
                        if trucScroller:
                            break

                if not trucScroller:  # on ne zoom que si on ne se sert pas de la molette dans le menu au-dessus
                    before_x_pos = (width/2 - scroll[0]) / zoom
                    before_y_pos = (height/2 - scroll[1]) / zoom

                    zoom = zoom+event.y/14

                    after_x_pos = (width/2 - scroll[0]) / zoom
                    after_y_pos = (height/2 - scroll[1]) / zoom

                    scroll[0] += (after_x_pos - before_x_pos) * zoom
                    scroll[1] += (after_y_pos - before_y_pos) * zoom

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                mouseDownTime = pygame.time.get_ticks()  # on se sert de ce timing pour les menus et le dragging
                if curseur_alidad:
                    alidad = True
                    alidadPos = pygame.mouse.get_pos()
                elif curseur_cercles:
                    souris = pygame.mouse.get_pos()
                    cerclePos = ((souris[0] - scroll[0]) / zoom, (souris[1] - scroll[1]) / zoom)
                if menuRadar.checkActive():
                    if not menuRadar.checkMenuHovered():
                        menuRadar.window.hide()
                        menuRadarTimer = pygame.time.get_ticks()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and (curseur_alidad or curseur_cercles or curseur_aliSep):
                alidad = False
                curseur_alidad = False
                curseur_cercles = False
                curseur_aliSep = False
                pygame.mouse.set_cursor(pygame.cursors.arrow)

            elif (event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not (empecherDragging or
                  curseur_aliSep or curseur_alidad) and menuValeurs is None and menuATC is None
                  and mouseDownTime + dragDelay >= pygame.time.get_ticks()):

                if curseur_cercles:
                    curseur_cercles = False
                elif menuRadarTimer + dragDelay <= pygame.time.get_ticks():
                    menuRadar.show()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 2 and not empecherDragging and conflitGen:
                mouse = pygame.mouse.get_pos()
                conflitGen.computeSpawn(((mouse[0] - scroll[0]) / zoom, (mouse[1] - scroll[1]) / zoom), carte)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and empecherDragging:
                empecherDragging = False

            manager.process_events(event)

        if conflitGen is not None:
            conflitGen.checkScrollBar(carte)

        """Dragging"""

        if (pygame.mouse.get_pressed()[0] and not empecherDragging and
                dragDelay + mouseDownTime <= pygame.time.get_ticks()):
            pygame.mouse.set_cursor(pygame.cursors.ball)

            scroll[0] += pygame.mouse.get_pos()[0] - drag[0]
            scroll[1] += pygame.mouse.get_pos()[1] - drag[1]
            drag = [pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]]
        else:
            drag = [pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]]
            if not curseur_alidad and not curseur_aliSep and not curseur_cercles:
                pygame.mouse.set_cursor(pygame.cursors.arrow)

        """Keys"""

        keys = pygame.key.get_pressed()

        if not pressing and nouvelAvionWin is None and modifWindow is None:

            if keys[pygame.K_f] and flightDataWindow is None:  # Flight Data Window
                flightDataWindow = fdw.flightDataWindow()
                pressing = True
                delaiPressage = pygame.time.get_ticks()

                # commandes pilote
            if keys[pygame.K_n] and nouvelAvionWin is None and pilote:
                nouvelAvionWin = interface.nouvelAvionWindow(carte['routes'], perfos)
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_DOWN]:
                pilote = False
            if keys[pygame.K_UP]:
                pilote = True

                # commandes temps et sauvegarde
            if keys[pygame.K_SPACE]:
                localRequests.append((0, 'Pause'))
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_LEFT]:
                pressing = True
                localRequests.append((0, 'Slower'))
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_RIGHT]:
                pressing = True
                localRequests.append((0, 'Faster'))
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_s]:
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_r]:
                pressing = True
                delaiPressage = pygame.time.get_ticks()

        elif pygame.time.get_ticks() - delaiPressage >= dragDelay:
            # on vérifie que plus aucune touche n'est pressée et on remet la variable à son état initial

            if keys[pygame.K_s]:
                localRequests.append((0, 'Save'))
                save_text_timing = pygame.time.get_ticks()

            if keys[pygame.K_r]:
                localRequests.append((0, 'Restart'))
            pressing = False

        # on se débarrasse des menus inutils
        if menuATC is not None:
            if not menuATC.checkAlive():
                menuATC = None

        if menuValeurs is not None:
            if not menuValeurs.checkAlive():
                menuValeurs = None

        if flightDataWindow is not None:
            if not flightDataWindow.checkAlive():
                flightDataWindow = None

        if nouvelAvionWin is not None:
            if not nouvelAvionWin.checkAlive():
                nouvelAvionWin = None

        if modifWindow is not None:
            if not modifWindow.checkAlive():
                modifWindow = None

        if menuRadar.checkActive():
            menuRadar.checkMenuHovered()

        '''partie affichage'''

        # on remplit d'abord avec une couleur
        win.fill((105, 105, 105))

        # on dessine les secteurs
        for zone in carte['zones'].values():
            liste_affichage_secteurs = []
            if carte_defs.check_is_zone_active(zone, game.heure):
                for point in zone['contour']:
                    pos = positionAffichage(point[0], point[1], zoom, scroll[0], scroll[1])
                    liste_affichage_secteurs.append((pos[0], pos[1]))
                pygame.draw.polygon(win, zone['couleur'], liste_affichage_secteurs)

        # on dessine les routes
        for segment in carte['lignes']['TRANSIT']:
            pygame.draw.line(win, (150, 150, 150), (segment[0][0]*zoom + scroll[0], segment[0][1]*zoom + scroll[1]),
                             (segment[1][0]*zoom + scroll[0], segment[1][1]*zoom + scroll[1]), 1)

        for nom_segment, segment in carte['segments'].items():

            if carte_defs.check_is_segment_active(carte['segments'][nom_segment], game.heure, carte['zones']):
                point1 = carte['points'][segment['points'][0]['name']]

                for point in segment['points']:
                    point2 = carte['points'][point['name']]
                    pygame.draw.line(win, (150, 150, 150),
                                     (point1[0] * zoom + scroll[0], point1[1] * zoom + scroll[1]),
                                     (point2[0] * zoom + scroll[0], point2[1] * zoom + scroll[1]), 1)
                    point1 = point2

        # dessin des cercles concentriques
        if cerclePos is not None:

            for i in range(15):

                pygame.draw.circle(
                    win, (120, 120, 120),
                    (cerclePos[0] * zoom + scroll[0], cerclePos[1] * zoom + scroll[1]),
                    10 * i / mapScale * zoom, 1
                )

        # on dessine les points
        for nom, point in carte['points'].items():
            pygame.draw.polygon(win, (155, 155, 155), ((point[0]*zoom + scroll[0], point[1]*zoom - 2 + scroll[1]), (point[0]*zoom + 2 + scroll[0], point[1]*zoom+2 + scroll[1]), (point[0]*zoom-2 + scroll[0], point[1]*zoom+2 + scroll[1])), 1)
            # img = font.render(nom, True, (155, 155, 155))
            # win.blit(img, (point[0]*zoom + 10 + scroll[0], point[1]*zoom+10 + scroll[1]))

        # on affiche les avions

        if conflitGen is not None:
            conflitGen.draw(win, zoom, scroll)
            color = [10, 10, 10]
            for avion in dictAvionsAff.values():
                if color[0] <= 255 - 40:
                    color[0] += 70
                elif color[1] <= 255 - 40:
                    color[0] = 255
                    color[1] += 70
                elif color[2] <= 255 - 40:
                    color[1] = 255
                    color[2] += 70
                avion.drawEstimatedRoute(carte['points'], conflitGen.temps, color, win, zoom, scroll)

        for avion in dictAvionsAff.values():
            avion.draw(win, zoom, scroll, vecteurs, vecteurSetting, carte['points'], game.heure)

        # on affiche les boutons
        manager.update(time_delta)
        manager.draw_ui(win)

        if not game.paused:  # oui en fait quand c en pause c False
            img = font.render("gelé", True, (255, 105, 180))
            win.blit(img, (20, 50))

        if game.accelerationTemporelle != 1:
            img = font.render(str(game.accelerationTemporelle), True, (255, 105, 180))
            win.blit(img, (20, 70))

        # dessin Heure
        heureDisplay = horloge.affichageHeure(game.heure)

        img = font.render(heureDisplay, True, (255, 105, 180))
        win.blit(img, (20, 20))

        # dessin alidad
        if alidad:
            pygame.draw.line(win, (70, 140, 240), alidadPos, pygame.mouse.get_pos(), 2)
            distance = round(math.sqrt((alidadPos[0] - pygame.mouse.get_pos()[0]) ** 2 +
                                       (alidadPos[1] - pygame.mouse.get_pos()[1]) ** 2) / zoom * mapScale, 1)
            img = font.render(str(distance), True, (70, 140, 240))
            win.blit(img, (pygame.mouse.get_pos()[0] + 20, pygame.mouse.get_pos()[1]))

        if pygame.time.get_ticks() - temps_affichage_text <= save_text_timing:
            img = font.render("Sauvegardé", True, (70, 140, 240))
            win.blit(img, ((width - img.get_width())/2, (height - img.get_height())/2))

        # prise des screenshots
        if pygame.time.get_ticks() >= dernierScreen + delaiScreen and replayMode and not pilote:
            capture.saveScreenshot(win, dossierScreen / (horloge.heureXML(game.heure) + '.png'))
            dernierScreen = pygame.time.get_ticks()

        # Envoi des packets.
        # On fait avec un try and except au cas où un paquet se perde

        try:
            if localRequests is not []:
                packetId = (packetId + 1) % 100  # l'Id du paquet permet au serveur de mettre en ordre les données
                packet = Packet(packetId, game=game, requests=localRequests)
            else:
                packet = Packet(game)
                packetId = packet.Id
            packet = n.send(packet)
        except:  # dans le cas où l'on perd un paquet, on garde les données précédentes
            print('Paquet perdu')
            packet = tempoPacket
        pygame.display.update()


main(address)
