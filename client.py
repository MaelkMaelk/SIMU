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




def main(server_ip):
    global temps
    global height
    global width
    run = True

    # menus
    menuAvion = None
    menuOptionsATC = MenuATC((0, 0), 0, 0)
    menuOptionsATC.kill()

    # on se connecte au serveur
    n = Network(server_ip)
    packet = n.getP()

    i = 0
    packetId = 0
    while packet == None and i < 200:
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

    # scroll and zoom
    zoomDef = 0.5
    scrollDef = [width / 4, height/4]
    zoom = zoomDef
    scroll = scrollDef
    drag = [0, 0]
    dragging = False

    # vecteurs et type
    vecteurs = False
    affichage_type_avion = False
    vecteurSetting = 6

    # fenetre nouvel avion
    nouvelAvionWin = None
    selectedRoute = None
    selectedAircraft = None
    selectedAircraftButton = None
    selectedRouteButton = None
    selectedFL = None
    selectedPFL = None
    selectedIndicatif = 'FCACA'
    conflitGen = False
    conflitAvion = None  # l'avion avec lequel on veut un conflit
    conflitPoint = None  # le point ou on veut le conflit
    selectConflitState = 0  # états possibles : inactif 0, avion 1, point 2, spawn 3

    # pour qu'on n'ait qu'un seul appui par touche
    pressing = False
    delaiPressage = pygame.time.get_ticks()

    # pilote
    pilote = False

    while run:
        localRequests = []
        tempoPacket = packet

        time_delta = clock.tick(40) / 1000.0
        clock.tick(40)

        for avionId, avion in packet.dictAvions.items():  # on parcourt le paquet qu'on a reçu du serveur

            if avionId in dictAvionsAff.keys():  # si l'avion est deja dans notre liste locale
                # on l'update avec la methode update de la classe avion
                dictAvionsAff[avionId].update(avion, zoom, scroll)
            else:  # sinon
                # on l'ajoute avec methode update de la classe dict
                dictAvionsAff.update({avionId: Avion(avionId, avion)})

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

        triggered = False  # si un bouton est pressé, on s'en sert pour ne pas drag alors qu'on voulait appuyer bouton

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
            if event.type == pygame.MOUSEWHEEL:
                zoom = zoom+event.y/14

                scroll[0] = width/2 * (1 - zoom)
                scroll[1] = height/2 * (1 - zoom)

            if event.type == pygame_gui.UI_BUTTON_START_PRESS and not curseur_alidad and selectConflitState == 0:
                '''faut mettre le menu quelque part ici'''
                if menuAvion is not None:
                    modifications = menuAvion.checkEvent(event)
                    if modifications is not None:
                        avionId = modifications[0]
                        modifications = modifications[1]

                        for changement, valeur in modifications.items():
                            localRequests.append((avionId, changement, valeur))

                triggered = True

                if event.ui_element == menuOptionsATC.partBouton and event.mouse_button == 1:
                    avionId = menuOptionsATC.kill()
                    localRequests.append((avionId, 'Part'))
                elif event.ui_element == menuOptionsATC.movBouton and event.mouse_button == 1:
                    avionId = menuOptionsATC.kill()
                    localRequests.append((avionId, 'Mouvement'))
                elif event.ui_element == menuOptionsATC.montrerBouton and event.mouse_button == 1:
                    avionId = menuOptionsATC.kill()
                    localRequests.append((avionId, 'Montrer'))
                elif event.ui_element == menuOptionsATC.FLBouton and event.mouse_button == 1:
                    avionId = menuOptionsATC.kill()
                    localRequests.append((avionId, 'FL?'))
                else:
                    for avion in dictAvionsAff.values():

                        if event.ui_element == avion.bouton:
                            if event.mouse_button == 2 and not pilote:
                                localRequests.append((avion.Id, 'Warning'))
                            elif event.mouse_button == 2:
                                avion.onFrequency = not avion.onFrequency
                            elif event.mouse_button == 1:
                                avion.etiquettePos +=1
                            elif event.mouse_button == 1:
                                avion.etiquettePos += 1
                            elif event.mouse_button == 3 and pilote:
                                localRequests.append((avion.Id, 'Remove'))

                        elif event.ui_element == avion.etiquette.bouton:
                            if event.mouse_button == 1 and pilote:
                                menuAvion = interface.menuAvion(avion, map)

                        # Menu de selection nouvel avion
                if nouvelAvionWin is not None:
                    if event.ui_element in nouvelAvionWin.avionsBoutons:
                        for bouton in range(len(nouvelAvionWin.avionsBoutons)):
                            if event.ui_element == nouvelAvionWin.avionsBoutons[bouton]:
                                selectedAircraft = list(nouvelAvionWin.avions.keys())[bouton]
                                selectedAircraftButton = nouvelAvionWin.avionsBoutons[bouton]
                            else:
                                nouvelAvionWin.avionsBoutons[bouton].unselect()

                    elif event.ui_element in nouvelAvionWin.routesBoutons:
                        for bouton in range(len(nouvelAvionWin.routesBoutons)):
                            if event.ui_element == nouvelAvionWin.routesBoutons[bouton]:
                                selectedRoute = nouvelAvionWin.routesFull[bouton]
                                selectedRouteButton = nouvelAvionWin.routesBoutons[bouton]
                            else:
                                nouvelAvionWin.routesBoutons[bouton].unselect()
                    elif event.ui_element == nouvelAvionWin.validationBouton and len(dictAvionsAff) != 0 and conflitGen:
                        selectConflitState = 1
                        pygame.mouse.set_cursor(pygame.cursors.diamond)
                        conflitGen = False
                        nouvelAvionWin.kill()
                        nouvelAvionWin = None

                    elif event.ui_element == nouvelAvionWin.validationBouton :
                        nouvelAvionWin.kill()
                        nouvelAvionWin = None
                        conflitGen = False
                        if selectedRoute is not None and selectedAircraft is not None:
                            localRequests.append((len(dictAvions), "Add",
                                                 AvionPacket(carte, len(dictAvions), selectedIndicatif,
                                                             selectedAircraft, perfos[selectedAircraft],
                                                             selectedRoute, FL=selectedFL, PFL=selectedPFL)))
                            selectedRoute = None
                            selectedAircraft = None
                            selectedRouteButton = None
                            selectedAircraftButton = None
                            selectedFL = None
                            selectedIndicatif = 'FCACA'

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and nouvelAvionWin is not None:
                if event.ui_element == nouvelAvionWin.conflitsBouton:
                    conflitGen = not conflitGen
                    if nouvelAvionWin.conflitsBouton.is_selected:
                        nouvelAvionWin.conflitsBouton.unselect()
                    else:
                        nouvelAvionWin.conflitsBouton.select()

            elif event.type == pygame_gui.UI_BUTTON_START_PRESS and not curseur_alidad and selectConflitState == 1:
                for avion in dictAvionsAff.values():
                    if event.ui_element == avion.bouton and event.mouse_button == 3 and selectConflitState == 1:
                        conflitAvion = avion
                        selectConflitState = 2
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and selectConflitState == 2:
                conflitPoint = ((pygame.mouse.get_pos()[0] - scroll[0]/zoom),
                                (pygame.mouse.get_pos()[1] - scroll[1]/zoom))
                speedRatio = conflitAvion.papa.speedGS/perfos[selectedAircraft][0]
                selectConflitState = 3
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and selectConflitState == 3:
                spawnPoint = ((pygame.mouse.get_pos()[0] - scroll[0])/zoom,
                                (pygame.mouse.get_pos()[1] - scroll[1])/zoom)
                selectConflitState = 0
                localRequests.append((len(dictAvions), "Add", AvionPacket(map, len(dictAvions), selectedIndicatif,
                                                             selectedAircraft, perfos[selectedAircraft], selectedRoute, x=spawnPoint[0], y=spawnPoint[1],
                                                             FL=selectedFL, PFL=selectedPFL)))
                AvionPacket(map, len(dictAvions), selectedIndicatif,
                            selectedAircraft, perfos[selectedAircraft],
                            selectedRoute, FL=selectedFL, PFL=selectedPFL)
                pygame.mouse.set_cursor(pygame.cursors.arrow)


            elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
                if event.ui_element == nouvelAvionWin.FLinput:
                    try:
                        selectedFL = int(event.text)
                    except:
                        selectedFL = 310
                elif event.ui_element == nouvelAvionWin.PFLinput:
                    try:
                        selectedPFL = int(event.text)
                    except:
                        selectedPFL = None
                elif event.ui_element == nouvelAvionWin.indicatifinput:
                    selectedIndicatif = event.text

            elif event.type == pygame_gui.UI_WINDOW_CLOSE:
                if nouvelAvionWin is not None:
                    if event.ui_element == nouvelAvionWin.window:
                        nouvelAvionWin.kill()
                        nouvelAvionWin = None
            # dragging
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and drag == [0, 0] and not curseur_alidad:
                drag = [pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]]
                dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not curseur_alidad:
                dragging = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and curseur_alidad:
                alidad = True
                alidadPos = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and curseur_alidad:
                alidad = False
                curseur_alidad = False
                pygame.mouse.set_cursor(pygame.cursors.arrow)

            manager.process_events(event)
        if menuAvion is not None:
            menuAvion.checkSliders()
        if selectedRouteButton is not None:
            selectedRouteButton.select()
        if selectedAircraftButton is not None:
            selectedAircraftButton.select()
        if triggered:
            dragging = False
            drag = [0, 0]

        keys = pygame.key.get_pressed()

        if dragging:
            scroll[0] += pygame.mouse.get_pos()[0] - drag[0]
            scroll[1] += pygame.mouse.get_pos()[1] - drag[1]
            drag = [pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]]
        else:
            drag = [0, 0]

        if not pressing and nouvelAvionWin is None:
            if keys[pygame.K_r]: # reset zoom & scroll
                zoom = zoomDef
                scroll = scrollDef
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_a]:  # alidad start
                curseur_alidad = True
                pygame.mouse.set_cursor(pygame.cursors.broken_x)
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_3]:  # vecteurs
                vecteurSetting = 3
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_t]:  # type avions
                affichage_type_avion = not affichage_type_avion
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
            if keys[pygame.K_n] and nouvelAvionWin is None and pilote:
                nouvelAvionWin = NouvelAvionWindow(carte['routes'], perfos)
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_DOWN]:
                pilote = False
            if keys[pygame.K_UP]:
                pilote = True
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
            pressing = False

        win.fill((55, 65, 75))
        for secteur in carte['secteurs']:
            liste_affichage_secteurs = []
            for point in secteur['contour']:
                pos = positionAffichage(point[0], point[1], zoom, scroll[0], scroll[1])
                liste_affichage_secteurs.append((pos[0], pos[1]))
            pygame.draw.polygon(win, secteur['couleur'], liste_affichage_secteurs)

        for segment in carte['segments']['STAR']:
            pygame.draw.line(win, (105, 110, 105), (segment[0][0]*zoom + scroll[0], segment[0][1]*zoom + scroll[1]),
                             (segment[1][0]*zoom + scroll[0], segment[1][1]*zoom + scroll[1]), 2)

        for nom, point in carte['points'].items():

            pygame.draw.polygon(win, (155, 155, 155), ((point[0]*zoom + scroll[0], point[1]*zoom - 2 + scroll[1]), (point[0]*zoom + 2 + scroll[0], point[1]*zoom+2 + scroll[1]), (point[0]*zoom-2 + scroll[0], point[1]*zoom+2 + scroll[1])), 1)
            #img = font.render(nom, True, (155, 155, 155))
            #win.blit(img, (point[0]*zoom + 10 + scroll[0], point[1]*zoom+10 + scroll[1]))
        if pilote:
            for avion in dictAvionsAff.values():
                avion.draw(win, zoom, scroll, vecteurs, vecteurSetting, affichage_type_avion)
        else:
            for avion in dictAvionsAff.values():
                avion.draw(win, zoom, scroll, vecteurs, vecteurSetting, affichage_type_avion)

        manager.draw_ui(win)
        manager.update(time_delta)

        if selectConflitState == 3:
            # on convertit la position du cercle pour l'affichage
            pos = positionAffichage(conflitPoint[0], conflitPoint[1], zoom, scroll[0], scroll[1])
            # on détermine le rayon du cercle
            conflitRadius = math.sqrt((conflitPoint[0] - conflitAvion.papa.x) ** 2 + (conflitPoint[1] - conflitAvion.papa.y) ** 2) \
                            / speedRatio

            # on dessine les trois cercles
            pygame.draw.circle(win, (255, 0, 0), (pos[0], pos[1]),
                               conflitRadius*zoom, 1)

            pygame.draw.circle(win, (71, 123, 146), (pos[0], pos[1]),
                               (conflitRadius - 15/mapScale) * zoom, 1)

            pygame.draw.circle(win, (71, 123, 146), (pos[0], pos[1]),
                               (conflitRadius + 15/mapScale) * zoom, 1)

        if not game.paused:  # oui en fait quand c en pause c False
            img = font.render("gelé", True, (255, 105, 180))
            win.blit(img, (20, 50))

        # dessin Heure
        heures = str(round(game.heure//3600))
        if len(heures) == 1:
            heures = '0' + heures
        minutes = str(round(game.heure % 3600//60))
        if len(minutes) == 1:
            minutes = '0' + minutes

        img = font.render(heures + ':' + minutes, True, (255, 105, 180))
        win.blit(img, (20, 20))

        # dessin alidad
        if alidad:
            pygame.draw.line(win, (255, 105, 180), alidadPos, pygame.mouse.get_pos())
            distance = round(math.sqrt((alidadPos[0] - pygame.mouse.get_pos()[0]) ** 2 +
                                       (alidadPos[1] - pygame.mouse.get_pos()[1]) ** 2) / zoom * mapScale, 1)
            img = font.render(str(distance), True, (255, 105, 180))
            win.blit(img, (pygame.mouse.get_pos()[0] + 20, pygame.mouse.get_pos()[1]))

        try:
            if localRequests is not []:
                packetId = (packetId + 1) % 100
                packet = Packet(packetId, game=game, requests=localRequests)
            else:
                packet = Packet(game)
                packetId = packet.Id
            packet = n.send(packet)

        except:
            print('Paquet perdu')
            packet = tempoPacket
        pygame.display.update()


main(address)
