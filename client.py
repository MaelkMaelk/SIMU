import pygame
from network import Network
from player import *
import pygame_gui
import math

pygame.init()
width = 1200
height = 1000

win = pygame.display.set_mode((width, height))
manager = pygame_gui.UIManager((width, height),'theme.json')

pygame.display.set_caption("Client")
temps = pygame.time.get_ticks()

clock = pygame.time.Clock()


def main():
    global temps
    global height
    global width
    run = True
    # menus
    menuRoulant = menuDeroulant(0, 0, "altitude", 152)
    menuPoints = MenuRoute((0, 0), 0, 0, {'BOJOL': (900, 10, True)})
    menuPoints.kill()
    menuOptionsATC = MenuATC((0, 0), 0, 0)
    menuOptionsATC.kill()
    n = Network()
    packet = n.getP()
    i = 0

    packetId = 0
    while packet == None and i < 2000:
        n = Network()
        packet = n.getP()
        i +=1

    perfos = packet.perfos
    dictAvionsAff = {}
    dictAvions = packet.dictAvions

    font = pygame.font.SysFont(None, 18)

    # Map
    map = packet.map
    listePoints = map[0]
    listeSecteur = map[1]
    listeSegments = map[2]
    listeRoutes = map[3]
    mapScale = 0.0814
    # scroll and zoom
    zoom = 0.5
    scroll = [-100, 20]
    drag = [0,0]
    dragging = False

    # alidad
    alidad = False
    alidadPos = (0, 0)
    alidadStart = False

    # vecteurs et type
    vecteurs = False
    typeAff = False
    vecteurSetting = 6

    # fenetre nouvel avion
    nouvelAvionWin = None
    selectedRoute = None
    selectedAircraft = None
    selectedAircraftButton = None
    selectedRouteButton = None
    selectedFL = 310
    selectedPFL = 310
    selectedIndicatif = 'FCACA'
    conflitGen = False
    conflitAvion = None  # l'avion avec lequel on veut un conflit
    conflitPoint = None  # le point ou on veut le conflit
    selectConflitState = 0  # états possibles : inactif 0, avion 1, point 2, spawn 3

    # pour qu'on ai qu'un seul appui par touche
    pressing = False
    delaiPressage = pygame.time.get_ticks()

    # pilote
    pilote = False


    while run:
        toBeRemoved = []
        localRequests = []
        tempoPacket = packet

        time_delta = clock.tick(40) / 1000.0
        clock.tick(40)

        for avionId, avion in packet.dictAvions.items():
            if avionId in dictAvionsAff.keys():  # si l'avion est deja dans notre liste locale
                # on l'update avec la methode update de la classe avion
                dictAvionsAff[avionId].update(avion, zoom, scroll, mapScale)
            else:  # sinon
                # on l'ajoute avec methode update de la classe dict
                dictAvionsAff.update({avionId: Avion(avionId, avion, mapScale)})
                dictAvionsAff[avionId].etiquetteGen(manager)

        if len(dictAvionsAff) > len(packet.dictAvions):  # si on a plus d'avions local qu'on en reçoi
            toBeRemovedOther = []
            print(dictAvionsAff.keys())

            for avionId in dictAvionsAff.keys():  # on itere sur la boucle locale
                # si on trouve un avion local qui n'est pas dans les données reçues
                if avionId not in list(packet.dictAvions.keys()):
                    print('caca')
                    toBeRemovedOther.append(avionId)
            print(toBeRemovedOther)
            for avionId in toBeRemovedOther:
                # 2eme boucle pour supprimer car on peut pas delete en pleine iteration
                dictAvionsAff[avionId].kill()
                dictAvionsAff.pop(avionId)
        game = packet.game
        dictAvions = packet.dictAvions

        triggered = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
            if event.type == pygame.MOUSEWHEEL:
                zoom = zoom+event.y/14
            if event.type == pygame_gui.UI_BUTTON_START_PRESS and not alidadStart and selectConflitState == 0:
                triggered = True

                if event.ui_element in menuRoulant.boutonList:
                    if event.ui_element == menuRoulant.boutonList[0]:
                        menuRoulant.increase()
                    elif event.ui_element == menuRoulant.boutonList[-1]:
                        menuRoulant.decrease()
                    else:
                        Idcouple = menuRoulant.kill()
                        localRequests.append((Idcouple, menuRoulant.what, int(event.ui_element.text)))
                elif event.ui_element in menuPoints.boutonList:
                    Idcouple = menuPoints.kill()
                    localRequests.append((Idcouple, 'Direct', event.ui_element.text))
                elif event.ui_element == menuOptionsATC.partBouton and event.mouse_button == 1:
                    Idcouple = menuOptionsATC.kill()
                    localRequests.append((Idcouple, 'Part'))
                elif event.ui_element == menuOptionsATC.movBouton and event.mouse_button == 1:
                    Idcouple = menuOptionsATC.kill()
                    localRequests.append((Idcouple, 'Mouvement'))
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
                        elif event.ui_element == avion.PFLbouton:
                            menuRoulant.kill()
                            menuRoulant.generate(avion.Id, avion.PFLbouton.get_abs_rect()[0],
                                                 avion.PFLbouton.get_abs_rect()[1], "PFL",
                                                 avion.PFL)
                        elif event.ui_element == avion.indicatifBouton:
                            if event.mouse_button == 1 and pilote:
                                menuRoulant.kill()
                                menuRoulant.generate(avion.Id, avion.indicatifBouton.get_abs_rect()[0],
                                                     avion.indicatifBouton.get_abs_rect()[1], "Heading",
                                                     round(avion.heading))
                            elif event.mouse_button == 3:
                                avion.drawRoute = True
                            elif event.mouse_button == 2 and not pilote:
                                localRequests.append((avion.Id, 'Part'))
                            elif event.mouse_button == 1 and not pilote:
                                menuOptionsATC = MenuATC(avion.Id, avion.indicatifBouton.get_abs_rect()[0],
                                                         avion.indicatifBouton.get_abs_rect()[1])
                        elif event.ui_element == avion.altitudeBouton and pilote:
                            if event.mouse_button == 1:
                                menuRoulant.kill()
                                menuRoulant.generate(avion.Id, avion.altitudeBouton.get_abs_rect()[0],
                                                     avion.altitudeBouton.get_abs_rect()[1], "Altitude",
                                                     avion.targetFL)
                        elif event.ui_element == avion.routeBouton and pilote:
                            if event.mouse_button == 1:
                                menuPoints = MenuRoute(avion.Id, avion.altitudeBouton.get_abs_rect()[0],
                                                     avion.altitudeBouton.get_abs_rect()[1], avion.route)

                        elif event.ui_element == avion.sortieBouton and pilote:
                            localRequests.append((avion.Id, 'Mouvement'))

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

                    elif event.ui_element == nouvelAvionWin.validationBouton and not conflitGen:
                        nouvelAvionWin.kill()
                        nouvelAvionWin = None
                        if selectedRoute is not None and selectedAircraft is not None:
                            localRequests.append((len(dictAvions), "Add",
                                                 AvionPacket(mapScale, len(dictAvions), selectedIndicatif,
                                                             selectedAircraft, perfos[selectedAircraft],
                                                             selectedRoute[0][0], selectedRoute[0][1],
                                                             selectedFL, selectedRoute, PFL=selectedPFL)))
                            selectedRoute = None
                            selectedAircraft = None
                            selectedRouteButton = None
                            selectedAircraftButton = None
                            selectedFL = 310
                            selectedIndicatif = 'FCACA'
                    elif event.ui_element == nouvelAvionWin.validationBouton:
                        selectConflitState = 1
                        pygame.mouse.set_cursor(pygame.cursors.diamond)
                        conflitGen = False
                        nouvelAvionWin.kill()
                        nouvelAvionWin = None
            elif event.type == pygame_gui.UI_BUTTON_PRESSED and nouvelAvionWin is not None:
                if event.ui_element == nouvelAvionWin.conflitsBouton:
                    conflitGen = not conflitGen
                    if nouvelAvionWin.conflitsBouton.is_selected:
                        nouvelAvionWin.conflitsBouton.unselect()
                    else:
                        nouvelAvionWin.conflitsBouton.select()

            elif event.type == pygame_gui.UI_BUTTON_START_PRESS and not alidadStart and selectConflitState == 1:
                for avion in dictAvionsAff.values():
                    if event.ui_element == avion.bouton and event.mouse_button == 3 and selectConflitState == 1:
                        conflitAvion = avion
                        selectConflitState = 2
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and selectConflitState == 2:
                conflitPoint = ((pygame.mouse.get_pos()[0] - plotSize - scroll[0])/zoom,
                                (pygame.mouse.get_pos()[1] - plotSize - scroll[1])/zoom)
                speedRatio = conflitAvion.speedPacket/perfos[selectedAircraft][0]
                conflitRadius = math.sqrt((conflitPoint[0] - conflitAvion.x)**2 + (conflitPoint[1] - conflitAvion.y)**2)\
                                /speedRatio
                selectConflitState = 3
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and selectConflitState == 3:
                spawnPoint = ((pygame.mouse.get_pos()[0] - plotSize - scroll[0])/zoom,
                                (pygame.mouse.get_pos()[1] - plotSize - scroll[1])/zoom)
                selectConflitState = 0
                localRequests.append((len(dictAvions), "Add", AvionPacket(mapScale, len(dictAvions),
                                                                         selectedIndicatif, selectedAircraft,
                                                                         perfos[selectedAircraft],
                                                                         spawnPoint[0], spawnPoint[1],selectedFL,
                                                                         selectedRoute, PFL=selectedPFL)))
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
                        selectedPFL = selectedFL
                elif event.ui_element == nouvelAvionWin.indicatifinput:
                    selectedIndicatif = event.text

            elif event.type == pygame_gui.UI_WINDOW_CLOSE:
                if nouvelAvionWin is not None:
                    if event.ui_element == nouvelAvionWin.window:
                        nouvelAvionWin.kill()
                        nouvelAvionWin = None
                elif event.ui_element == menuRoulant.cont:
                    menuRoulant.kill()

            # dragging
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and drag == [0, 0] and not alidadStart:
                drag = [pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]]
                dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not alidadStart:
                dragging = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and alidadStart:
                alidad = True
                alidadPos = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and alidadStart:
                alidad = False
                alidadStart = False
                pygame.mouse.set_cursor(pygame.cursors.arrow)

            manager.process_events(event)
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
                zoom = 0.5
                scroll = [-100, 20]
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_a]:  # alidad start
                alidadStart = True
                pygame.mouse.set_cursor(pygame.cursors.broken_x)
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_3]:  # vecteurs
                vecteurSetting = 3
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_t]:  # type avions
                typeAff = not typeAff
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
                nouvelAvionWin = NouvelAvionWindow(listeRoutes, perfos)
                pressing = True
                delaiPressage = pygame.time.get_ticks()
            if keys[pygame.K_DOWN]:
                pilote = False
            if keys[pygame.K_UP]:
                pilote = True
        elif True not in pygame.key.ScancodeWrapper() and pygame.time.get_ticks() - delaiPressage >= 150:
            pressing = False



        win.fill((70, 70, 70))
        affListeSecteur = []
        for point in listeSecteur:
            affListeSecteur.append((point[0]*zoom+plotSize+scroll[0], point[1]*zoom+plotSize+scroll[1]))
        pygame.draw.polygon(win, (55, 55, 55), affListeSecteur)


        for segment in listeSegments:
            pygame.draw.line(win, (105, 110, 105), (segment[0][0]*zoom + scroll[0]+plotSize, segment[0][1]*zoom + scroll[1]+plotSize),
                             (segment[1][0]*zoom + scroll[0]+plotSize, segment[1][1]*zoom + scroll[1]+plotSize), 2)

        '''for nom, point in listePoints.items():
            pygame.draw.polygon(win, (155, 155, 155), ((point[0]*zoom + scroll[0], point[1]*zoom-10 + scroll[1]), (point[0]*zoom+7 + scroll[0], point[1]*zoom+7 + scroll[1]), (point[0]*zoom-7 + scroll[0], point[1]*zoom+7 + scroll[1])), 1)
            img = font.render(nom, True, (155, 155, 155))
            win.blit(img, (point[0]*zoom + 10 + scroll[0], point[1]*zoom+10 + scroll[1]))'''
        if pilote:
            for avion in dictAvionsAff.values():
                avion.drawPilote(win, zoom, scroll, vecteurs, vecteurSetting, typeAff)
        else:
            for avion in dictAvionsAff.values():
                avion.draw(win, zoom, scroll, vecteurs, vecteurSetting, typeAff)

        manager.draw_ui(win)
        manager.update(time_delta)

        if alidad:
            pygame.draw.line(win, (255,105,180), alidadPos, pygame.mouse.get_pos())
            distance = round(math.sqrt((alidadPos[0] - pygame.mouse.get_pos()[0])**2 +
                                 (alidadPos[1] - pygame.mouse.get_pos()[1])**2)/zoom*mapScale, 1)
            img = font.render(str(distance), True, (255,105,180))
            win.blit(img, (pygame.mouse.get_pos()[0] + 20, pygame.mouse.get_pos()[1]))

        if selectConflitState == 3:
            pygame.draw.circle(win, (255, 0, 0), (conflitPoint[0]*zoom + scroll[0]+plotSize,
                                                  conflitPoint[1]*zoom + scroll[1]+plotSize),
                               conflitRadius*zoom, 1)
            pygame.draw.circle(win, (71, 123, 146), (conflitPoint[0] * zoom + scroll[0] + plotSize,
                                                  conflitPoint[1] * zoom + scroll[1] + plotSize),
                               (conflitRadius - 15/mapScale) * zoom, 1)
            pygame.draw.circle(win, (71, 123, 146), (conflitPoint[0] * zoom + scroll[0] + plotSize,
                                                  conflitPoint[1] * zoom + scroll[1] + plotSize),
                               (conflitRadius + 15/mapScale) * zoom, 1)

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

main()
