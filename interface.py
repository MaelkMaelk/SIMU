import pygame
import pygame_gui


def selectButtonInList(liste, event):
    for bouton in liste:
        if bouton == event:
            bouton.disable()
        else:
            bouton.enable()


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
                                                        text=('Cap - ' + str(round(avion.papa.heading))))
        self.headingContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (100, 200)),
                                                                         container=self.window)
        tempo = scrollListGen(range(round(avion.papa.heading / 5) * 5 - 25, round(avion.papa.heading / 5) * 5 + 30, 5),
                              pygame.Rect((0, 0), (75, 17)), self.headingContainer)
        self.headingBoutonListe = tempo[1]
        self.headingSlider = tempo[0]
        self.headingSlider.set_scroll_from_start_percentage((round(avion.papa.heading / 5) * 5 - 15) / 300 * 0.8)

        # génération boutons Alti
        self.altiLabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 17), (100, 17)),
                                                     container=self.window,
                                                     text=('FL - ' + str(round(avion.papa.altitude / 100))),
                                                     anchors={'left': 'left', 'left_target': self.headingLabel})
        self.altiContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (100, 200)),
                                                                      container=self.window, anchors={'left': 'left',
                                                                                                      'left_target': self.headingContainer})
        tempo = scrollListGen(range(round(avion.papa.altitude / 1000) * 10 - 50, round(avion.papa.altitude / 1000) * 10 + 60, 10),
                              pygame.Rect((0, 0), (75, 17)), self.altiContainer)
        self.altiBoutonListe = tempo[1]
        self.altiSlider = tempo[0]
        self.altiSlider.set_scroll_from_start_percentage((round(avion.papa.altitude / 1000) * 10 - 30) / 410 * 0.8)

        # génération boutons speed
        self.speedLabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 17), (100, 17)),
                                                      container=self.window, text=('IAS - ' + str(avion.papa.speedIAS)),
                                                      anchors={'left': 'left', 'left_target': self.altiLabel})
        self.speedContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (100, 200)),
                                                                       container=self.window, anchors={'left': 'left',
                                                                                                       'left_target': self.altiContainer})
        tempo = scrollListGen(range(round(avion.papa.speedIAS / 10) * 10 - 50, round(avion.papa.speedIAS / 10) * 10 + 60, 10),
                              pygame.Rect((0, 0), (75, 17)), self.speedContainer)
        self.speedBoutonListe = tempo[1]
        self.speedSlider = tempo[0]
        self.speedSlider.set_scroll_from_start_percentage((round(avion.papa.speedIAS / 10) * 10 - 100) / 330 * 0.8)

        # génération boutons points

        self.pointContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (100, 200)),
                                                                       container=self.window, anchors={'left': 'left',
                                                                                                       'left_target': self.speedContainer})
        tempo = scrollListGen([point['name'] for point in avion.papa.route['points']], pygame.Rect((0, 0), (75, 17)),
                              self.pointContainer, sliderBool=False)
        self.pointBoutonListe = tempo[1]
        print('cacz')

        # génération boutons next routes

        self.routeContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (100, 200)),
                                                                       container=self.window, anchors={'left': 'left',
                                                                                                       'left_target': self.pointContainer})

        tempo = scrollListGen([route for route in avion.papa.route['sortie']], pygame.Rect((0, 0), (75, 17)),
                              self.routeContainer, sliderBool=False)
        self.routeBoutonliste = tempo[1]
        print(self.routeBoutonliste)

        # bouton validation

        self.validerBouton = pygame_gui.elements.UIButton(pygame.Rect((200, 90), (75, 17)), text='valider',
                                                          container=self.window,
                                                          anchors={'top': 'top', 'top_target': self.pointContainer})

        # dict pour les valeurs que le menu renverra
        self.returnValues = {}

    def checkSliders(self):

        """
        Change la valeur des boutons en fonction de la position du slider, pour tout le menu
        """

        selectedValue = None
        if self.headingSlider.has_moved_recently:
            if 'Heading' in self.returnValues:
                selectedValue = self.returnValues['Heading']

            value = round(
                (360 - 5 * (len(self.headingBoutonListe) - 1)) * (self.headingSlider.start_percentage / 0.8) / 5) * 5
            for bouton in self.headingBoutonListe:
                bouton.text = str(value)
                bouton.rebuild()
                if selectedValue == value:
                    bouton.disable()
                else:
                    bouton.enable()
                value += 5

        elif self.altiSlider.has_moved_recently:
            if 'Altitude' in self.returnValues:
                selectedValue = self.returnValues['Altitude']

            # la valeur de niveau oscille entre 0 et 410
            value = round(
                (410 - 10 * (len(self.headingBoutonListe) - 1)) * (self.altiSlider.start_percentage / 0.8) / 10) * 10
            for bouton in self.altiBoutonListe:
                bouton.text = str(value)
                bouton.rebuild()
                if selectedValue == value:
                    bouton.disable()
                else:
                    bouton.enable()
                value += 10

        elif self.speedSlider.has_moved_recently:
            if 'IAS' in self.returnValues:
                selectedValue = self.returnValues['IAS']

            value = round((330 - 10 * (len(self.headingBoutonListe) - 1)) * (
                    self.speedSlider.start_percentage / 0.8) / 10) * 10 + 70
            for bouton in self.speedBoutonListe:
                bouton.text = str(value)
                bouton.rebuild()
                if selectedValue == value:
                    bouton.disable()
                else:
                    bouton.enable()
                value += 10

    def checkEvent(self, event):

        """Vérifie si un des boutons du menu a été pressé et modifie les données en conséquence
        :returns: le dictionaire de valeurs si on valide, None sinon"""

        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            print('caca')

            # heading
        elif event.ui_element in self.headingBoutonListe:

            self.returnValues.update({'Heading': int(event.ui_element.text)})
            selectButtonInList(self.headingBoutonListe, event.ui_element)
            # on enlève le direct pour ne pas faire de confusion
            if 'Direct' in self.returnValues:
                self.returnValues.pop('Direct')

            # ALTI
        elif event.ui_element in self.altiBoutonListe:

            self.returnValues.update({'Altitude': int(event.ui_element.text) * 100})
            selectButtonInList(self.altiBoutonListe, event.ui_element)

            # speed
        elif event.ui_element in self.speedBoutonListe:

            selectButtonInList(self.speedBoutonListe, event.ui_element)
            self.returnValues.update({'IAS': int(event.ui_element.text)})

            # direct
        elif event.ui_element in self.pointBoutonListe:

            selectButtonInList(self.pointBoutonListe, event.ui_element)
            self.returnValues.update({'Direct': event.ui_element.text})
            if 'Heading' in self.returnValues:
                self.returnValues.pop('Heading')

            # route
        elif event.ui_element in self.routeBoutonliste:

            selectButtonInList(self.routeBoutonliste, event.ui_element)
            self.returnValues.update({'Route': event.ui_element.text})

        elif event.ui_element is self.validerBouton:

            self.window.kill()
            return self.avion.Id, self.returnValues


class etiquetteAPS:

    def __init__(self, avion):

        self.evolution = avion.papa.altitudeEvoTxt

        self.text = avion.papa.indicatif + str(round(avion.papa.altitude/100)) + self.evolution + '   M' + str(round(avion.papa.speedIAS/10))
        self.bouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (80, 34)),
            text='self.text', object_id=pygame_gui.core.ObjectID('@etiquette', 'button'))

    def update(self, avion):

        self.evolution = avion.papa.altitudeEvoTxt

        if avion.etiquettePos % 4 == 0:
            Xvalue = 0
            Yvalue = -34
        elif avion.etiquettePos % 4 == 1:
            Xvalue = 0
            Yvalue = 0
        elif avion.etiquettePos % 4 == 2:
            Xvalue = -80
            Yvalue = 0
        else:
            Xvalue = -80
            Yvalue = -34

        self.text = avion.papa.indicatif + '\n' + str(round(avion.papa.altitude/100)) + self.evolution + '   M' + str(
            round(avion.papa.speedIAS/10))
        self.bouton.rect = pygame.Rect((avion.etiquetteX + Xvalue, avion.etiquetteY + Yvalue), (80, 34))
        self.bouton.text = self.text
        self.bouton.rebuild()
        self.bouton.show()

    def kill(self):
        self.bouton.kill()