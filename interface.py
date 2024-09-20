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


class NouvelAvionWindow:

    def __init__(self, routes, avions):

        # le dictionnaire utilisé pour renvoyer les valeurs sélectionnées par nos boutons
        self.returnValues = {'indicatif': 'FCACA', 'avion': 'B738', 'FL': 310, 'PFL': 310}

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

        self.validerBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 5), (200, 17)),
            text='Ok',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.conflitsBouton, 'left': 'left', 'left_target': self.routeContainer})

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

            event.ui_element.select()
            self.returnValues.update({'avion': event.ui_element.text})

        elif event.ui_element in self.routeBoutonListe:

            event.ui_element.select()
            self.returnValues.update({'route': event.ui_element.text})

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

        tempo = scrollListGen([route for route in avion.papa.route['sortie']],
                              pygame.Rect((0, 0), (75, 17)),
                              self.routeContainer,
                              sliderBool=False)

        self.routeBoutonliste = tempo[1]

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

            # route
        elif event.ui_element in self.routeBoutonliste:

            selectButtonInList(self.routeBoutonliste, event.ui_element)
            self.returnValues.update({'Route': event.ui_element.text})

        elif event.ui_element is self.validerBouton:

            self.window.kill()
            return self.avion.Id, self.returnValues

class etiquette:

    def __init__(self, avion):

        self.extended = False  # relate de si l'étiquette est étendue ou non

        self.container = pygame_gui.elements.UIAutoResizingContainer(
            pygame.Rect((0, 0), (0, 0)), pygame.Rect((0, 0), (0, 0)), resize_top=False, resize_left=False)

        self.speedGS = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(avion.papa.speedGS)[:2],
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            container=self.container)

        self.indicatif = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=avion.papa.indicatif,
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.speedGS},
            container=self.container)

        self.type_dest = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            text=avion.papa.aircraft + " " + "LFVB",
            anchors={'top': 'top', 'top_target': self.speedGS},
            container=self.container
        )

        self.AFL = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(round(avion.papa.altitude/100)),
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.CFL = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(round(avion.papa.altitude / 100))[:2],
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif,},
            container=self.container)

        self.DCT = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=avion.papa.nextPoint['name'],
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.speedIAS = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text="S",
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.rate = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text="R",
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.indicatif},
            container=self.container)

        self.XPT = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=avion.papa.route['points'][-1]['name'],
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.XFL = pygame_gui.elements.UIButton(  # #TODO associer XFL ici
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(avion.papa.XFL),
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.PFL = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(avion.papa.PFL),
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.nextSector = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text="I2",
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.ligneDeux = [self.indicatif, self.type_dest]
        self.ligneTrois = [self.AFL, self.CFL, self.DCT, self.speedIAS, self.rate]
        self.ligneQuatre = [self.XPT, self.XFL, self.PFL, self.nextSector]

    def update(self, avion):

        """
        On ajuste tous les paramètres de l'étiquette : sa position ainsi que les valeurs textes dans les boutons
        """

        # on ajuste la position du container en fonction de son point cardinal par rapport au plot
        if avion.etiquettePos % 4 == 0:
            Xvalue = 0
            Yvalue = - self.container.get_rect()[3]
        elif avion.etiquettePos % 4 == 1:
            Xvalue = 0
            Yvalue = 0
        elif avion.etiquettePos % 4 == 2:
            Xvalue = - self.container.get_rect()[2]
            Yvalue = 0
        else:
            Xvalue = - self.container.get_rect()[2]
            Yvalue = - self.container.get_rect()[3]

        self.boutonAgauche()  # TODO utiliser cette fonction que quand c'est nécessaire

        # speed et C/D rate
        if avion.papa.evolution == 0:  # on affiche la rate que si l'avion est en evo
            evo = ""
        else:
            evo = "  " + str(avion.papa.evolution)[:3]

        self.speedGS.set_text(str(avion.papa.speedGS)[:2] + evo)

        # alti
        self.AFL.set_text(str(round(avion.papa.altitude/100)) + " " + avion.papa.altitudeEvoTxt)

        self.CFL.set_text(str(avion.papa.PFL))  # TODO appeler les changements textes CFL etc que quand on les change

        # container
        self.container.set_position((avion.etiquetteX + Xvalue, avion.etiquetteY + Yvalue))
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


def updateDistanceGauche(liste):
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
