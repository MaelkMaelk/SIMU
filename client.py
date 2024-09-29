import pygame
import horloge
from network import Network
import server_browser
from player import *
import pygame_gui
import interface
from paquets_avion import *
import math

# recherche de tous les serveurs sur le réseau
address = server_browser.serverBrowser()
print(address)

# fenêtre Pygame, mettre en 1920, 1080 pour plein écran
pygame.init()
width = 1000
height = 1000

win = pygame.display.set_mode((width, height))
manager = pygame_gui.UIManager((width, height), 'theme.json')

pygame.display.set_caption("Client")
temps = pygame.time.get_ticks()
clock = pygame.time.Clock()
font = pygame.font.SysFont('arial', 18)


def main(server_ip: str):
    global temps
    global height
    global width
    run = True

    distance = 10
    # menus
    menuAvion = None
    menuATC = None
    menuValeurs = None
    flightDataWindow = None

    # on se connecte au serveur
    n = Network(server_ip)
    packet = n.getP()

    i = 0
    packetId = 0
    while packet is None and i < 200:
        n = Network(server_ip)
        packet = n.getP()
        i +=1

    perfos = packet.perfos
    game = packet.game
    dictAvionsAff = {}
    dictAvions = packet.dictAvions

    # Map
    carte = packet.map
    mapScale = carte['mapScale']

    # alidad
    alidad = False
    alidadPos = (0, 0)
    curseur_alidad = False

    # alisep
    curseur_aliSep = False
    sepA = interface.aliSep('A')
    sepB = interface.aliSep('B')

    # scroll and zoom
    zoomDef = 0.5
    scrollDef = [width / 4, height/4]
    zoom = zoomDef
    scroll = scrollDef
    drag = [0, 0]
    dragging_delay = 350  # il y a un délai avant de pouvoir drag (pour pouvoir ouvrir les menus notamment)
    mouseDownTime = 0
    empecherDragging = False

    # vecteurs et type
    vecteurs = False
    affichage_type_avion = False
    vecteurSetting = 6

    # fenêtre nouvel avion
    nouvelAvionWin = None

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
        game = packet.game
        dictAvions = packet.dictAvions

        sepA.calculation(carte)
        sepB.calculation(carte)

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
            elif event.type == pygame_gui.UI_BUTTON_PRESSED and not curseur_alidad:
                empecherDragging = False

                # on regarde si notre menu pour le pilote est actif
                if menuAvion is not None:

                    # si on valide les modifs, alors la fonction checkEvent retourne les modifs
                    modifications = menuAvion.checkEvent(event)
                    if modifications:

                        # on applique alors les modifs
                        avionId = modifications[0]
                        modifications = modifications[1]

                        # pour chaque modif, on prépare une requête au serveur
                        for changement, valeur in modifications.items():
                            localRequests.append((avionId, changement, valeur))

                if menuATC is not None:

                    # si on valide les modifs, alors la fonction checkEvent retourne les modifs
                    action = menuATC.checkEvent(event)
                    if action:
                        if type(action) in [list, tuple]:  # si c'est un tuple alors cela correspond à une requête
                            localRequests.append(action)

                if menuValeurs is not None:

                    # si on valide les modifs, alors la fonction checkEvent retourne les modifs
                    action = menuValeurs.checkEvent(event)
                    if action:
                        if type(action) in [list, tuple]:  # si c'est un tuple alors cela correspond à une requête
                            localRequests.append(action)
                        elif action in ['HDG', 'DCT']:
                            menuValeurs = interface.menuValeurs(menuValeurs.avion, pygame.mouse.get_pos(), action)

                if curseur_aliSep:
                    for avion in dictAvionsAff.values():
                        if avion.checkClicked(event):
                            if curseur_aliSep == 'A':
                                if sepA.linkAvion(avion, carte):
                                    curseur_aliSep = False
                                    pygame.mouse.set_cursor(pygame.cursors.arrow)
                            else:
                                if sepB.linkAvion(avion, carte):
                                    curseur_aliSep = False
                                    pygame.mouse.set_cursor(pygame.cursors.arrow)

                else:
                    for avion in dictAvionsAff.values():  # pour chaque avion

                        action = avion.checkEvent(event, pilote)  # on vérifie si l'event est associé avec ses boutons

                        if type(action) in [list, tuple]:  # si c'est un tuple alors cela correspond à une requête
                            localRequests.append(action)

                        elif action == 'menuPIL' and menuAvion is None:  # si c'est menu alors, on vérifie qu'on peut menu
                            menuAvion = interface.menuAvion(avion)

                        elif action == 'menuATC' and menuATC is None:
                            menuATC = interface.menuATC(avion, pygame.mouse.get_pos())

                        elif menuValeurs is None and action is not None:
                            # si on a renvoyé autre chose alors c'est une valeur pour ouvrir un menu
                            menuValeurs = interface.menuValeurs(avion, pygame.mouse.get_pos(), action)

                    # Menu de selection nouvel avion
                    # si notre menu est ouvert
                    if nouvelAvionWin is not None:
                        # si on appuie sur le bouton valider, alors le menu renvoie les valeurs
                        newPlaneData = nouvelAvionWin.checkEvent(event)

                        # on vérifie que newPlane n'est pas None (les valeurs ont été renvoyés)
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
                                FL=FL,
                                PFL=PFL)

                            localRequests.append((len(dictAvions), "Add", newPlane))

            elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
                nouvelAvionWin.checkFields(event)

            if menuAvion or nouvelAvionWin:
                pass

            # zoom géré ici
            elif event.type == pygame.MOUSEWHEEL:
                cacaAuPipi = True
                if menuValeurs is not None:
                    cacaAuPipi = menuValeurs.checkScrolled(event)

                if cacaAuPipi:  # on ne zoom que si on ne se sert pas de la molette dans le menu au-dessus
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

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and curseur_alidad:
                alidad = False
                curseur_alidad = False
                pygame.mouse.set_cursor(pygame.cursors.arrow)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and curseur_aliSep:
                curseur_aliSep = False
                pygame.mouse.set_cursor(pygame.cursors.arrow)

            manager.process_events(event)

        if menuAvion is not None:
            menuAvion.checkSliders()

        """Dragging"""

        if (pygame.mouse.get_pressed()[0] and not empecherDragging and
                dragging_delay + mouseDownTime <= pygame.time.get_ticks()):
            pygame.mouse.set_cursor(pygame.cursors.ball)

            scroll[0] += pygame.mouse.get_pos()[0] - drag[0]
            scroll[1] += pygame.mouse.get_pos()[1] - drag[1]
            drag = [pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]]
        else:
            drag = [pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]]
            if not curseur_alidad and not curseur_aliSep:
                pygame.mouse.set_cursor(pygame.cursors.arrow)

        """Keys"""

        keys = pygame.key.get_pressed()

        if not pressing and nouvelAvionWin is None:

            if keys[pygame.K_r]:  # reset zoom & scroll
                zoom = zoomDef
                scroll = scrollDef
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_t]:  # type avions
                affichage_type_avion = not affichage_type_avion
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_a]:  # alidad start
                curseur_alidad = True
                pygame.mouse.set_cursor(pygame.cursors.broken_x)
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_g]:  # alidad start
                sepA.kill()
                curseur_aliSep = 'A'
                pygame.mouse.set_cursor(pygame.cursors.diamond)
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_h]:  # alidad start
                sepB.kill()
                curseur_aliSep = 'B'
                pygame.mouse.set_cursor(pygame.cursors.diamond)
                pressing = True
                delaiPressage = pygame.time.get_ticks()

            if keys[pygame.K_f] and flightDataWindow is None:  # Flight Data Window
                flightDataWindow = interface.flightDataWindow()
                pressing = True
                delaiPressage = pygame.time.get_ticks()

            # commandes pour vecteurs
            if keys[pygame.K_3]:
                vecteurSetting = 3
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_6]:
                vecteurSetting = 6
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_9]:
                vecteurSetting = 9
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_v]:
                vecteurs = not vecteurs
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
                localRequests.append((0, 'Slower'))
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_RIGHT]:
                localRequests.append((0, 'Faster'))
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_s]:
                localRequests.append((0, 'Save'))
                delaiPressage = pygame.time.get_ticks()
        elif True not in pygame.key.ScancodeWrapper() and pygame.time.get_ticks() - delaiPressage >= 150:
            # on vérifie que plus aucune touche n'est pressée et on remet la variable à son état initial
            pressing = False

        # on se débarrasse des menus inutils
        if menuAvion is not None:
            if not menuAvion.checkAlive():
                menuAvion = None

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

        '''partie affichage'''

        # on remplit d'abord avec une couleur
        win.fill((90, 90, 90))

        # on dessine les secteurs
        for secteur in carte['secteurs']:
            liste_affichage_secteurs = []
            for point in secteur['contour']:
                pos = positionAffichage(point[0], point[1], zoom, scroll[0], scroll[1])
                liste_affichage_secteurs.append((pos[0], pos[1]))
            pygame.draw.polygon(win, secteur['couleur'], liste_affichage_secteurs)

        # on dessine les routes
        for segment in carte['segments']['TRANSIT']:
            pygame.draw.line(win, (150, 150, 150), (segment[0][0]*zoom + scroll[0], segment[0][1]*zoom + scroll[1]),
                             (segment[1][0]*zoom + scroll[0], segment[1][1]*zoom + scroll[1]), 1)

        # on dessine les points
        for nom, point in carte['points'].items():
            pygame.draw.polygon(win, (155, 155, 155), ((point[0]*zoom + scroll[0], point[1]*zoom - 2 + scroll[1]), (point[0]*zoom + 2 + scroll[0], point[1]*zoom+2 + scroll[1]), (point[0]*zoom-2 + scroll[0], point[1]*zoom+2 + scroll[1])), 1)
            # img = font.render(nom, True, (155, 155, 155))
            # win.blit(img, (point[0]*zoom + 10 + scroll[0], point[1]*zoom+10 + scroll[1]))

        # on affiche les avions
        if pilote:
            for avion in dictAvionsAff.values():
                avion.draw(win, zoom, scroll, vecteurs, vecteurSetting, carte['points'])
        else:
            for avion in dictAvionsAff.values():
                avion.draw(win, zoom, scroll, vecteurs, vecteurSetting, carte['points'])

        # on affiche les boutons
        manager.update(time_delta)
        manager.draw_ui(win)

        if not game.paused:  # oui en fait quand c en pause c False
            img = font.render("gelé", True, (255, 105, 180))
            win.blit(img, (20, 50))

        # dessin Heure
        heureDisplay = horloge.affichageHeure(game.heure)

        img = font.render(heureDisplay, True, (255, 105, 180))
        win.blit(img, (20, 20))

        # dessin alidad
        if alidad:
            pygame.draw.line(win, (255, 105, 180), alidadPos, pygame.mouse.get_pos())
            distance = round(math.sqrt((alidadPos[0] - pygame.mouse.get_pos()[0]) ** 2 +
                                       (alidadPos[1] - pygame.mouse.get_pos()[1]) ** 2) / zoom * mapScale, 1)
            img = font.render(str(distance), True, (255, 105, 180))
            win.blit(img, (pygame.mouse.get_pos()[0] + 20, pygame.mouse.get_pos()[1]))

        # envoi des packets
        # on fait avec un try and except au cas où un paquet se perde

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
