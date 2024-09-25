import pygame
import pygame_gui
import horloge


def selectButtonInList(liste: list, event):
    for bouton in liste:
        if bouton == event:
            bouton.select()
        else:
            bouton.unselect()


def scrollListGen(valueList, rect, container, sliderBool=True, sliderDroite=False):
    """Fonction qui construit une liste de boutons, avec une scrollbar width 17
    :arg valueList: liste des valeurs en txt ou autre peu importe
    :arg rect: taille des boutons
    :arg container: conteneur Pygame_gui dans lequel on met les boutons
    :parameter sliderBool: Bool, si on veut un slider ou non. True par defaut
    :parameter sliderDroite: Bool, si on veut le slider à droite ou non
    :return (slider, listeBoutons)"""

    valueList = list(valueList)

    if sliderBool:
        slider = pygame_gui.elements.UIVerticalScrollBar(
            relative_rect=pygame.Rect((0, 0), (17, container.get_abs_rect()[3])), container=container,
            visible_percentage=0.2)
        if not sliderDroite:
            boutonAnchor = {'left': 'left', 'left_target': slider}
        else:
            boutonAnchor = {}
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

    if sliderDroite:
        decalage = liste[0].get_abs_rect()[2]
        slider.set_relative_position((decalage, 0))

    return slider, liste


class nouvelAvionWindow:

    def __init__(self, routes, avions):

        # le dictionnaire utilisé pour renvoyer les valeurs sélectionnées par nos boutons
        self.returnValues = {'indicatif': 'FCACA', 'avion': 'B738', 'arrival': False}

        # la fenêtre du menu
        self.window = pygame_gui.elements.UIWindow(pygame.Rect((250, 250), (600, 400)))

        # la liste des routes
        self.routeContainer = pygame_gui.elements.UIScrollingContainer(
            pygame.Rect((0, 34), (150, 200)), container=self.window, allow_scroll_x=False)

        self.routeBoutonListe = scrollListGen(list(routes.keys()),
                                              pygame.Rect((0, 0), (125, 17)), self.routeContainer, False)[1]

        # la liste des types avion
        self.typeAvionContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (150, 200)),
        container=self.window, anchors={'left': 'left', 'left_target': self.routeContainer}, allow_scroll_x=False)

        self.typeAvionBoutonListe = scrollListGen(
            list(avions.keys()), pygame.Rect((0, 0), (125, 17)), self.typeAvionContainer, False)[1]

        # les divers autres boutons et champs

        self.conflitsBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 20), (200, 17)),
            text='Générateur de conflits',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.typeAvionContainer, 'left': 'left', 'left_target': self.routeContainer})

        self.arrivalBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 5), (200, 17)),
            text='Arrivée?',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.conflitsBouton, 'left': 'left',
                     'left_target': self.routeContainer})

        self.validerBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 5), (200, 17)),
            text='Ok',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.arrivalBouton, 'left': 'left', 'left_target': self.routeContainer})

        self.indicatiflabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer},
            text='Indicatif')

        self.indicatifinput = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((0, 0), (200, 30)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top', 'top_target': self.indicatiflabel})

        self.FLlabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top', 'top_target': self.indicatifinput},
            text='FL')

        self.FLinput = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((0, 0), (200, 30)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top', 'top_target': self.FLlabel})

        self.PFLlabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top', 'top_target': self.FLinput},
            text='PFL')

        self.PFLinput = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((0, 0), (200, 30)), container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top', 'top_target': self.PFLlabel})

    def checkEvent(self, event):

        """
        Vérifie si un des boutons ou textbox du menu a été pressé ou modifié, et modifie les données en conséquence
        :arg event: l'évenement qu'il faut vérifier
        :returns: le dictionaire de valeurs si on valide, None sinon
        """

        # on vérifie d'abord les champs de text
        if event.ui_element in self.typeAvionBoutonListe:

            selectButtonInList(self.typeAvionBoutonListe, event.ui_element)
            self.returnValues.update({'avion': event.ui_element.text})

        elif event.ui_element in self.routeBoutonListe:

            selectButtonInList(self.routeBoutonListe, event.ui_element)
            self.returnValues.update({'route': event.ui_element.text})

        elif event.ui_element == self.arrivalBouton:
            self.returnValues['arrival'] = not self.returnValues['arrival']
            if not self.arrivalBouton.is_selected:
                self.arrivalBouton.select()
            else:
                self.arrivalBouton.unselect()

        elif event.ui_element == self.validerBouton:
            self.window.kill()
            return self.returnValues

    def checkFields(self, event):

        # on vérifie le FL
        if event.ui_element == self.FLinput:
            try:
                self.returnValues.update({'FL': int(event.text)})

            except:  # si l'utilisateur rentre n'importe quoi, on remet à la valeur de base
                self.returnValues.update({'FL': 310})

        # on vérifie le PFL
        elif event.ui_element == self.PFLinput:
            try:
                self.returnValues.update({'PFL': int(event.text)})

            except:  # si l'utilisateur rentre n'importe quoi, on remet à la valeur du FL
                self.returnValues.update({'PFL': self.returnValues['FL']})

        # on vérifie l'indicatif
        elif event.ui_element == self.indicatifinput:
            self.returnValues.update({'indicatif': event.text})

    def kill(self):
        self.window.kill()

    def checkAlive(self):
        return self.window.alive()


class menuAvion:

    def __init__(self, avion, gameMap):
        self.avion = avion
        self.window = self.window = pygame_gui.elements.UIWindow(pygame.Rect((400, 400), (600, 350)))

        # génération boutons heading
        self.headingLabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 17), (100, 17)),
            container=self.window,
            text=('Cap - ' + str(round(avion.papa.heading))))

        self.headingContainer = pygame_gui.elements.UIScrollingContainer(
            pygame.Rect((0, 34), (100, 200)),
            container=self.window)

        tempo = scrollListGen(range(round(avion.papa.heading / 5) * 5 - 25, round(avion.papa.heading / 5) * 5 + 30, 5),
                              pygame.Rect((0, 0), (75, 17)), self.headingContainer)

        self.headingBoutonListe = tempo[1]
        self.headingSlider = tempo[0]
        self.headingSlider.set_scroll_from_start_percentage((round(avion.papa.heading / 5) * 5 - 15) / 300 * 0.8)

        # génération boutons Alti
        self.altiLabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 17), (100, 17)),
            container=self.window,
            text=('FL - ' + str(round(avion.papa.altitude / 100))),
            anchors={'left': 'left', 'left_target': self.headingLabel})

        self.altiContainer = pygame_gui.elements.UIScrollingContainer(
            pygame.Rect((0, 34), (100, 200)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.headingContainer})

        tempo = scrollListGen(
            range(round(avion.papa.altitude / 1000) * 10 - 50, round(avion.papa.altitude / 1000) * 10 + 60, 10),
            pygame.Rect((0, 0), (75, 17)), self.altiContainer)

        self.altiBoutonListe = tempo[1]
        self.altiSlider = tempo[0]

        self.altiSlider.set_scroll_from_start_percentage((round(avion.papa.altitude / 1000) * 10 - 30) / 410 * 0.8)

        # génération boutons speed
        self.speedLabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 17), (100, 17)),
            container=self.window, text=('IAS - ' + str(avion.papa.speedIAS)),
            anchors={'left': 'left', 'left_target': self.altiLabel})

        self.speedContainer = pygame_gui.elements.UIScrollingContainer(
            pygame.Rect((0, 34), (100, 200)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.altiContainer})

        tempo = scrollListGen(range(round(avion.papa.speedIAS / 10) * 10 - 50, round(avion.papa.speedIAS / 10) * 10 + 60, 10),
                              pygame.Rect((0, 0), (75, 17)), self.speedContainer)

        self.speedBoutonListe = tempo[1]
        self.speedSlider = tempo[0]
        self.speedSlider.set_scroll_from_start_percentage((round(avion.papa.speedIAS / 10) * 10 - 100) / 330 * 0.8)

        # génération boutons points

        self.pointContainer = pygame_gui.elements.UIScrollingContainer(
            pygame.Rect((0, 0), (100, 200)),
            container=self.window,
            anchors={'left': 'left','left_target': self.speedContainer})

        tempo = scrollListGen([point['name'] for point in avion.papa.route['points']],
                              pygame.Rect((0, 0), (75, 17)),
                              self.pointContainer,
                              sliderBool=False)

        self.pointBoutonListe = tempo[1]

        # génération boutons next routes

        self.routeContainer = pygame_gui.elements.UIScrollingContainer(
            pygame.Rect((0, 0), (100, 200)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.pointContainer})

        # bouton validation

        self.validerBouton = pygame_gui.elements.UIButton(
            pygame.Rect((200, 90), (75, 17)),
            text='valider',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.pointContainer})

        # dict pour les valeurs que le menu renverra
        self.returnValues = {}

    def checkAlive(self):
        return self.window.alive()

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

        """
        Vérifie si un des boutons du menu a été pressé et modifie les données en conséquence
        :arg event: l'évenement qu'il faut vérifier
        :returns: le dictionaire de valeurs si on valide, None sinon
        """

        # heading
        if event.ui_element in self.headingBoutonListe:

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

        elif event.ui_element is self.validerBouton:

            self.window.kill()
            return self.avion.Id, self.returnValues


class etiquette:

    def __init__(self, avion):

        clicks = frozenset([pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])

        self.extended = True  # relate de si l'étiquette est étendue ou non

        self.container = pygame_gui.elements.UIAutoResizingContainer(
            pygame.Rect((0, 0), (0, 0)), pygame.Rect((0, 0), (0, 0)), resize_top=False, resize_left=False)

        self.speedGS = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text="[] " + str(avion.papa.speedGS)[:2],
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            container=self.container,
            generate_click_events_from=clicks)

        self.indicatif = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=avion.papa.indicatif,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.speedGS},
            container=self.container,
            generate_click_events_from=clicks)

        self.type_dest = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            text=avion.papa.aircraft + " " + avion.papa.destination,
            generate_click_events_from=clicks,
            anchors={'top': 'top', 'top_target': self.speedGS},
            container=self.container
        )

        self.AFL = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(round(avion.papa.altitude/100)),
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.CFL = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(round(avion.papa.altitude / 100))[:2],
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.DCT = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=avion.papa.DCT,
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.speedIAS = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text="S",
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.rate = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text="R",
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.XPT = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=avion.papa.route['points'][-1]['name'],
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.XFL = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text="x" + str(avion.papa.XFL)[:2],
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.PFL = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(avion.papa.PFL)[:2],
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.nextSector = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=avion.papa.nextSector,
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquetteBold', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.ligneDeux = [self.indicatif, self.type_dest]
        self.ligneTrois = [self.AFL, self.CFL, self.DCT, self.speedIAS, self.rate]
        self.ligneQuatre = [self.XPT, self.XFL, self.PFL, self.nextSector]

    def update(self, avion):

        """
        On ajuste la position ainsi que les valeurs textes dans les boutons
        """

        # on ajuste la position du container en fonction de son point cardinal par rapport au plot

        # speed et C/D rate
        if avion.papa.evolution == 0:  # on affiche la rate que si l'avion est en evo
            evo = ""
        else:
            evo = "    " + str(round(avion.papa.evolution / 100))

        if avion.papa.integreOrganique:
            if self.extended:
                tickBox = "{v} "
            else:
                tickBox = ""
        else:
            tickBox = "{} "

        self.speedGS.set_text(tickBox + str(avion.papa.speedGS)[:2] + evo)

        if not avion.papa.headingMode:
            self.DCT.set_text(avion.papa.DCT)
        elif self.extended:
            self.DCT.set_text("h" + str(avion.papa.selectedHeading))
        else:
            self.DCT.set_text("h")

        self.XPT.set_text(avion.papa.XPT)

        # alti
        self.AFL.set_text(str(round(avion.papa.altitude/100)) + " " + avion.papa.altitudeEvoTxt)

        self.CFL.set_text(str(avion.papa.CFL)[:2])

        self.PFL.set_text("p" + str(avion.papa.PFL)[:2])

        self.XFL.set_text("x" + str(avion.papa.XFL)[:2])

        self.boutonAgauche()  # TODO utiliser cette fonction que quand c'est nécessaire

        # container
        self.container.set_position((avion.etiquetteX + 0, avion.etiquetteY + 0))
        self.container.update_containing_rect_position()
        self.container.recalculate_abs_edges_rect()

    def boutonAgauche(self):

        """
        Méthode qui met les boutons le plus à gauche possible de l'étiquette en fonction des boutons visibles
        """

        for ligne in [self.ligneDeux, self.ligneTrois, self.ligneQuatre]:  # on le fait pour chaque ligne
            for numBouton in range(len(ligne)):  # on fait avec un range pour pouvoir tronquer la liste

                bouton = ligne[numBouton]  # on récupère le bouton
                if bouton.visible:
                    distance = updateDistanceGauche(ligne[:numBouton])
                else:
                    distance = 0
                bouton.set_relative_position((distance, 0))

    def kill(self):
        self.container.kill()


def updateDistanceGauche(liste) -> int:
    """
    Calcule de la distance à gauche pour un élément, en fonction de la non-visibilité de ses voisins de ligne sur
     sa gauche, pour qu'il soit le plus à gauche possible.

    :arg liste: Liste correspondant à la ligne à vérifier. Les éléments sont triés de la gauche vers la droite,
     et la liste ne comprend que les voisins à la gauche de l'élément en question
    :return les nouvelles ancres pour l'élément dans un dict:
    """
    liste = list(liste)
    liste.reverse()  # on inverse la ligne pour partir du voisin direct

    distance = 0

    if not liste:  # si la liste est vide, il n'a donc pas de voisins à gauche
        return 0  # on renvoie un 0 s'il n'y a pas d'élément sur sa gauche

    for element in liste:  # on parcourt tous les éléments à sa gauche
        if element.visible:
            distance += element.get_abs_rect()[2]  # on renvoie des ancres au 1er élément visible à sa gauche
    return distance


class menuATC:

    def __init__(self, avion, pos):

        """
        Menu de commandes pour l'avion.
        :param avion: À quel avion le menu doit-il être associé ?
        :param pos: vector2 (x, y) de la souris
        """

        self.avion = avion

        width = 80
        height = 120

        x = pos[0] - width/2
        y = pos[1] - 35

        if avion.papa.etatFrequence == 'previousFreq':
            text = 'FORCE ASSU'
        elif avion.papa.etatFrequence == 'previousShoot':
            text = 'ASSUME'
        elif avion.papa.etatFrequence == 'nextCoord':
            text = '119.8'
        elif avion.papa.etatFrequence == 'nextShoot':
            text = 'RECLAIM'
        else:
            text = ''

        self.window = pygame_gui.elements.UIWindow(pygame.Rect((x, y), (width, height)),
                                                   draggable=False,
                                                   window_display_title=avion.papa.indicatif)

        # On définit tout d'abord les boutons qui sont tous les temps présents
        self.locWarn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (width, -1)), text='WARN LOC',
            container=self.window)

        self.warn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (width, -1)), text='WARN POS',
            container=self.window, anchors={'top': 'top', 'top_target': self.locWarn})

        self.montrer = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (width, -1)), text='SHOW',
            container=self.window, anchors={'top': 'top', 'top_target': self.warn})

        self.halo = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (width, -1)), text='HALO',
            container=self.window, anchors={'top': 'top', 'top_target': self.montrer})

        if not text == '':  # si le bouton doit apparaître alors, il aura du texte

            self.freqAssume = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (width, -1)),
                text=text,
                container=self.window)

            self.locWarn.set_anchors({'top': 'top', 'top_target': self.freqAssume})  # on décale donc le locWarn dessous
            self.locWarn.rebuild()
            self.mvt = None

        else:  # s'il ny a pas de bouton de transfer, il y a un bouton mvt

            self.mvt = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (width, -1)), text='MVT',
                container=self.window, anchors={'top': 'top', 'top_target': self.halo})

            self.freqAssume = None  # on assigne None pour pouvoir faire les comparaisons dans checkEvent

    def checkEvent(self, event):

        if event.ui_element == self.freqAssume:
            self.kill()

            if self.freqAssume.text == 'FORCE ASSU':  # si on force assume, on passe direct en frequence
                return self.avion.Id, 'EtatFreq', 'inFreq'

            elif self.freqAssume.text == 'RECLAIM':  # si on reclaim, on revient en freq
                return self.avion.Id, 'EtatFreq', 'nextCoord'

            elif not self.freqAssume.text == '':
                return self.avion.Id, 'EtatFreq', None

        elif event.ui_element == self.mvt:
            self.kill()
            return self.avion.Id, 'EtatFreq', None

        elif event.ui_element == self.montrer:
            self.kill()
            return self.avion.Id, 'Montrer'

        elif event.ui_element == self.warn:
            self.kill()
            return self.avion.Id, 'Warning'

        elif event.ui_element == self.locWarn:
            self.kill()
            self.avion.locWarning = not self.avion.locWarning

        elif event.ui_element == self.halo:
            self.kill()
            return self.avion.Id, 'Halo'

    def kill(self):
        self.window.kill()

    def checkAlive(self):
        return self.window.alive()


class menuValeurs:

    def __init__(self, avion, pos: list[float, float], valeur: str):

        """
        Menu utilisé par le controleur pour changer les valeurs des différents champs
        :param avion:
        :param pos:
        :param valeur:
        """

        self.avion = avion
        self.valeur = valeur

        width = 60
        height = 240

        x = pos[0] - width / 2
        y = pos[1] - 35

        self.liste = []
        self.listeAff = []

        if valeur == 'DCT':
            self.liste = [point['name'] for point in self.avion.papa.route['points']]
            self.listeAff = self.liste[self.liste.index(avion.papa.nextPoint['name']):]

        elif valeur == 'XPT':  # la diff de liste est qu'on ne prend pas en compte les points de notre secteur ici
            self.liste = [point['name'] for point in self.avion.papa.route['points']]
            self.listeAff = self.liste[self.liste.index(avion.papa.XPT) - 1:]

        elif valeur in ['XFL', 'PFL', 'CFL']:
            self.liste = [*range(0, 600, 10)]
            self.liste.reverse()
            indexDuFL = self.liste.index(avion.papa.PFL)
            self.liste[indexDuFL] = "R" + str(avion.papa.PFL)
            self.listeAff = self.liste[indexDuFL - 4: indexDuFL + 5]

        self.window = pygame_gui.elements.UIWindow(pygame.Rect((x, y), (width, height)),
                                                   window_display_title=valeur)

        self.up = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (width, -1)),
            container=self.window,
            text="↑"
        )

        self.listeContainer = pygame_gui.elements.UIScrollingContainer(
            container=self.window,
            relative_rect=pygame.Rect((0, 0), (width, height)),
            allow_scroll_x=False,
            allow_scroll_y=False,
            anchors={'top': 'top', 'top_target': self.up}
        )

        self.down = pygame_gui.elements.UIButton(
            pygame.Rect((0, 0), (width, -1)),
            container=self.window,
            text="↓",
            anchors={'top': 'top', 'top_target': self.listeContainer}
        )

        tempo = scrollListGen(
            self.listeAff,
            pygame.Rect((0, 0), (width, -1)),
            self.listeContainer,
            sliderBool=False)

        if valeur in ['XFL', 'PFL', 'CFL']:  # on ramène la fenêtre au bon endroit pour la souris (sur le PFL)
            y = y - (self.up.get_abs_rect()[3]*4.5 + self.window.title_bar_height)
            self.window.set_position((x, y))
        self.listeBoutons = tempo[1]
        self.listeContainer.set_dimensions((width, len(self.listeAff) * self.up.get_abs_rect()[3]))
        self.window.set_dimensions(
            (width,
             self.listeContainer.get_abs_rect()[3] + 2 * self.up.get_abs_rect()[3] + self.window.title_bar_height * 2.2))

    def checkEvent(self, event):
        """
        Vérifies si un event est relié à ce menu et prend les actions en conséquence
        :param event: l'event à vérifier
        :return:
        """

        if event.ui_element == self.up:
            indexDebut = self.liste.index(self.listeAff[0])  # on regarde où commence la liste dans l'autre
            if indexDebut - 1 >= 0:  # cela vérifie qu'on n'est pas en butée de liste
                self.listeAff = self.liste[indexDebut - 1: indexDebut - 1 + len(self.listeAff)]
                self.scrollUpdate()

        elif event.ui_element == self.down:
            indexDebut = self.liste.index(self.listeAff[0])  # on regarde où commence la liste dans l'autre
            if indexDebut + len(self.listeAff) <= len(self.liste) - 1:  # cela vérifie qu'on n'est pas en butée de liste
                self.listeAff = self.liste[indexDebut + 1: indexDebut + 1 + len(self.listeAff)]
                self.scrollUpdate()

        elif event.ui_element in self.listeBoutons:
            self.kill()

            if event.ui_element.text[0] == 'R':  # si on a une value qui correspond au PFL, alors il faut enlever le R

                try:  # on essaye de convertir en int
                    valeur = int(event.ui_element.text[1:])
                except:  # si c'est autre chose, par ex, une directe alors, on assigne tt simplement la valeur
                    valeur = event.ui_element.text
            else:
                try:
                    valeur = int(event.ui_element.text)
                except:
                    valeur = event.ui_element.text

            return self.avion.Id, self.valeur, valeur

    def scrollUpdate(self) -> None:
        """
        Mets à jour la valeur et l'état des différents boutons lorsqu'il y a un scroll
        :return:
        """
        for index in range(len(self.listeBoutons)):
            bouton = self.listeBoutons[index]
            bouton.set_text(str(self.listeAff[index]))

    def checkHovered(self, event) -> None:
        """
        Regarde si un bouton direct est survolé pour déssiner la directe associée
        :param event:
        :return:
        """
        if self.valeur in ['DCT', 'XPT'] and self.checkAlive():
            if event.ui_element in self.listeBoutons:
                self.avion.pointDessinDirect = event.ui_element.text

    def checkUnHovered(self, event) -> None:
        """
        Regarde
        :param event:
        :return:
        """
        if self.valeur in ['DCT', 'XPT']:
            if event.ui_element in self.listeBoutons:
                self.avion.pointDessinDirect = None

    def kill(self):
        self.window.kill()
        self.avion.pointDessinDirect = None

    def checkAlive(self):
        return self.window.alive()


class flightDataWindow:

    def __init__(self):

        width = 400
        height = 150

        self.window = pygame_gui.elements.UIWindow(
            pygame.Rect((20, 20), (width, height)),
            window_display_title="Flight Data Window",
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc')
        )

        self.ligneUn = pygame_gui.elements.UILabel(
            pygame.Rect((0, 5), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
        )

        self.ligneDeux = pygame_gui.elements.UILabel(
            pygame.Rect((0, 0), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
            anchors={'top': 'top', 'top_target': self.ligneUn}
        )

        self.ligneTrois = pygame_gui.elements.UIButton(
            pygame.Rect((0, 2), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
            anchors={'top': 'top', 'top_target': self.ligneDeux}
        )

        self.ligneQuatre = pygame_gui.elements.UILabel(
            pygame.Rect((0, 2), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
            anchors={'top': 'top', 'top_target': self.ligneTrois}
        )

        self.ligneCinq = pygame_gui.elements.UILabel(
            pygame.Rect((0, 0), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
            anchors={'top': 'top', 'top_target': self.ligneQuatre}
        )

    def linkAvion(self, avion, points: list, heure) -> None:
        """
        Associe la FDW à un avion
        :param avion: L'avion auquel on doit s'associer
        :param points: La liste des points de la carte
        :param heure: L'heure courante, pour pouvoir calculer les estimées
        :return:
        """
        ETX = avion.papa.calculeEstimate(points, avion.papa.XPT)  # heure de sortie
        ETE = avion.papa.calculeEstimate(points, avion.papa.DCT)  # heure d'entrée

        ETE = horloge.affichageHeure(ETE + heure)
        ETX = horloge.affichageHeure(ETX + heure)

        couleur = avion.etiquette.indicatif.get_class_ids()[1]
        objectID = pygame_gui.core.ObjectID('@flightDataWindow', couleur)

        for label in [self.ligneUn, self.ligneDeux, self.ligneTrois, self.ligneQuatre, self.ligneCinq]:
            label.change_object_id(objectID)

        text = (str(avion.papa.indicatif) + '       ' + str(avion.papa.aircraft)
                + '          ' + avion.papa.modeA + '       | N' + str(avion.papa.speedIAS) + ' Ok8  OkR  OkW')
        self.ligneUn.set_text(text)

        text = avion.papa.callsignFreq + '                                           ' + avion.papa.medevac
        self.ligneDeux.set_text(text)

        text = (avion.papa.provenance + '   ' + avion.papa.destination + '  R' + str(avion.papa.PFL)
                + ' ' + str(round(avion.papa.altitude/100)) + ' ' + str(avion.papa.PFL)
                + '    ' + avion.papa.EPT + '      ' + avion.papa.XPT + '  X' + str(avion.papa.XFL))
        self.ligneTrois.set_text(text)

        text = ('C' + str(avion.papa.CFL) + '   ' + str(avion.papa.DCT) + '        S' + '      R                   |'
                + ETE + '          ' + ETX)
        self.ligneQuatre.set_text(text)

        if avion.papa.etatFrequence in ['nextCoord', 'nextShoot']:
            freq = avion.papa.nextFrequency
        else:
            freq = '               '

        text = ('RMRS                                                 ' + freq + '         '
                + avion.papa.nextSector)
        self.ligneCinq.set_text(text)

    def kill(self):
        self.window.kill()

    def checkAlive(self):
        return self.window.alive()



