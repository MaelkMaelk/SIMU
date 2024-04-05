import pygame
import pygame_gui


def scrollListGen(valueList, rect, container, sliderBool=True):
    """Fonction qui construit une liste de boutons, avec une scrollbar width 17 tout le temps à gauche
    :arg valueList: liste des valeurs en txt ou autre peu importe
    :arg rect: taille des boutons
    :parameter sliderBool: Bool, si on veut un slider ou non. True par defaut
    :arg container: conteneur Pygame_gui dans lequel on met les boutons
    :return (slider, listeBoutons)"""

    valueList = list(valueList)


    if sliderBool:
        slider = pygame_gui.elements.UIVerticalScrollBar(
            relative_rect=pygame.Rect((0, 0), (17, container.get_abs_rect()[3])), container=container,
            visible_percentage=0.2)
        boutonAnchor = {'left': 'left', 'left_target': slider}
    else:
        slider = None
        boutonAnchor = {}

    if not valueList:
        return slider, []

    liste = [pygame_gui.elements.UIButton(
        relative_rect=rect,
        text=str(valueList[0]),
        container=container, anchors=boutonAnchor)]

    for value in valueList[1:]:
        boutonAnchor.update({'top': 'top', 'top_target': liste[-1]})
        liste.append(pygame_gui.elements.UIButton(
            relative_rect=rect,
            text=str(value),
            container=container,
            anchors=boutonAnchor))

    return slider, liste


class menuAvion:

    def __init__(self, avion, gameMap):
        self.avion = avion
        self.window = self.window = pygame_gui.elements.UIWindow(pygame.Rect((400, 400), (600, 600)))

        # génération boutons heading
        self.headingLabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 17), (100, 17)),
                                                        container=self.window,
                                                        text=('Cap - ' + str(round(avion.heading))))
        self.headingContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (100, 200)),
                                                                         container=self.window)
        tempo = scrollListGen(range(round(avion.heading / 5) * 5 - 25, round(avion.heading / 5) * 5 + 30, 5),
                              pygame.Rect((0, 0), (75, 17)), self.headingContainer)
        self.headingBoutonListe = tempo[1]
        self.headingSlider = tempo[0]
        self.headingSlider.set_scroll_from_start_percentage((round(avion.heading / 5) * 5 - 15) / 300 * 0.8)

        # génération boutons Alti
        self.altiLabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 17), (100, 17)),
                                                     container=self.window,
                                                     text=('FL - ' + str(round(avion.altitude / 100))),
                                                     anchors={'left': 'left', 'left_target': self.headingLabel})
        self.altiContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (100, 200)),
                                                                      container=self.window, anchors={'left': 'left',
                                                                                                      'left_target': self.headingContainer})
        tempo = scrollListGen(range(round(avion.altitude / 1000) * 10 - 50, round(avion.altitude / 1000) * 10 + 60, 10),
                              pygame.Rect((0, 0), (75, 17)), self.altiContainer)
        self.altiBoutonListe = tempo[1]
        self.altiSlider = tempo[0]
        self.altiSlider.set_scroll_from_start_percentage((round(avion.altitude / 1000) * 10 - 30) / 410 * 0.8)

        # génération boutons speed
        self.speedLabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 17), (100, 17)),
                                                      container=self.window, text=('IAS - ' + str(avion.speedIAS)),
                                                      anchors={'left': 'left', 'left_target': self.altiLabel})
        self.speedContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (100, 200)),
                                                                       container=self.window, anchors={'left': 'left',
                                                                                                       'left_target': self.altiContainer})
        tempo = scrollListGen(range(round(avion.speedIAS / 10) * 10 - 50, round(avion.speedIAS / 10) * 10 + 60, 10),
                              pygame.Rect((0, 0), (75, 17)), self.speedContainer)
        self.speedBoutonListe = tempo[1]
        self.speedSlider = tempo[0]
        self.speedSlider.set_scroll_from_start_percentage((round(avion.speedIAS / 10) * 10 - 100) / 330 * 0.8)

        # génération boutons points

        self.pointContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (100, 200)),
                                                                       container=self.window, anchors={'left': 'left',
                                                                                                       'left_target': self.speedContainer})
        tempo = scrollListGen([point['name'] for point in avion.route], pygame.Rect((0, 0), (75, 17)),
                              self.pointContainer, sliderBool=False)
        self.pointBoutonListe = tempo[1]

        # génération boutons next routes

        self.routeContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (100, 200)),
                                                                       container=self.window, anchors={'left': 'left',
                                                                                                       'left_target': self.pointContainer})

        tempo = scrollListGen([route for route in avion.nextRouteListe], pygame.Rect((0, 0), (75, 17)),
                              self.routeContainer, sliderBool=False)
        self.routeBoutonliste = tempo[1]
        print(self.routeBoutonliste)

        # génération bouton interception

        self.axeContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (100, 85)),
                                                                     container=self.window, anchors={'left': 'left',
                                                                                                     'left_target': self.speedContainer,
                                                                                                     'top': 'top',
                                                                                                     'top_target': self.pointContainer})

        tempo = scrollListGen([axe[0] for axe in gameMap[5]], pygame.Rect((0, 0), (75, 17)),
                              self.axeContainer, sliderBool=False)
        self.axeBoutonListe = tempo[1]

        # bouton validation

        self.validerBouton = pygame_gui.elements.UIButton(pygame.Rect((200, 90), (75, 17)), text='valider',
                                                          container=self.window,
                                                          anchors={'top': 'top', 'top_target': self.pointContainer})

        ''' VALEURS que le Menu renvera:'''

        self.returnValues = {}

    def checkSliders(self):

        """
        change la valeur des boutons en fonction de la position du slider, pour tout le menu
        """

        if self.headingSlider.has_moved_recently:

            value = round(
                (360 - 5 * (len(self.headingBoutonListe) - 1)) * (self.headingSlider.start_percentage / 0.8) / 5) * 5
            for bouton in self.headingBoutonListe:
                bouton.text = str(value)
                bouton.rebuild()
                value += 5

        elif self.altiSlider.has_moved_recently:

            # la valeur de niveau oscille entre 0 et 410
            value = round(
                (410 - 10 * (len(self.headingBoutonListe) - 1)) * (self.altiSlider.start_percentage / 0.8) / 10) * 10
            for bouton in self.altiBoutonListe:
                bouton.text = str(value)
                bouton.rebuild()
                value += 10

        elif self.speedSlider.has_moved_recently:

            value = round((330 - 10 * (len(self.headingBoutonListe) - 1)) * (
                    self.speedSlider.start_percentage / 0.8) / 10) * 10 + 70
            for bouton in self.speedBoutonListe:
                bouton.text = str(value)
                bouton.rebuild()
                value += 10

    def checkEvent(self, event):

        """vérifie si un des boutons du menu a été pressé et modifie les données en conséquence
        :returns: le dictionaire de valeurs si on valide, None sinon"""

        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            print('caca')

            # heading
        elif event.ui_element in self.headingBoutonListe:

            self.returnValues.update({'Heading': int(event.ui_element.text)})
            try:  # on enlève la direct pour ne pas faire de confusion
                self.returnValues.pop('Direct')
            except:
                pass

            # ALTI
        elif event.ui_element in self.altiBoutonListe:

            self.returnValues.update({'Altitude': int(event.ui_element.text) * 100})

            # speed
        elif event.ui_element in self.speedBoutonListe:

            self.returnValues.update({'IAS': int(event.ui_element.text)})

            # direct
        elif event.ui_element in self.pointBoutonListe:

            self.returnValues.update({'Direct': event.ui_element.text})
            try:  # on enlève le heading pour ne pas faire de confusion
                self.returnValues.pop('Heading')
            except:
                pass

            # route
        elif event.ui_element in self.routeBoutonliste:

            self.returnValues.update({'Route': event.ui_element.text})

        elif event.ui_element in self.axeBoutonListe:

            self.returnValues.update({'Intercept': event.ui_element.text})

        elif event.ui_element is self.validerBouton:

            self.window.kill()
            return self.avion.Id, self.returnValues

        return None
