
# Module imports
import pygame
import pygame_gui
import Python.horloge as horloge
from Python.valeurs_config import *


def selectButtonInList(liste: list, event):
    for bouton in liste:
        if bouton == event:
            bouton.select()
        else:
            bouton.unselect()


def scrollListGen(valueList, rect, container, sliderBool=True, sliderDroite=False, objectID=None):
    """Fonction qui construit une liste de boutons, avec une scrollbar width 17
    :arg valueList: liste des valeurs en txt ou autre peu importe
    :arg rect: taille des boutons
    :arg container: conteneur Pygame_gui dans lequel on met les boutons
    :parameter sliderBool: Bool, si on veut un slider ou non. True par defaut
    :parameter sliderDroite: Bool, si on veut le slider à droite ou non
    :parameter objectID: Une option de thème optionnelle pour les boutons.
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
        container=container, anchors=boutonAnchor, object_id=objectID)]

    for value in valueList[1:]:
        boutonAnchor.update({'top': 'top', 'top_target': liste[-1]})
        liste.append(pygame_gui.elements.UIButton(
            relative_rect=rect,
            text=str(value),
            container=container,
            anchors=boutonAnchor,
            object_id=objectID))

    if sliderDroite:
        decalage = liste[0].get_abs_rect()[2]
        slider.set_relative_position((decalage, 0))

    return slider, liste


class nouvelAvionWindow:

    def __init__(self, routes, avions):

        # le dictionnaire utilisé pour renvoyer les valeurs sélectionnées par nos boutons
        self.returnValues = {'indicatif': 'FCACA', 'avion': 'B738', 'arrival': False, 'conflit': False}

        # la fenêtre du menu
        self.window = pygame_gui.elements.UIWindow(pygame.Rect((250, 250), (600, 400)))

        # la liste des routes
        self.routeContainer = pygame_gui.elements.UIScrollingContainer(
            pygame.Rect((0, 34), (150, 200)), container=self.window, allow_scroll_x=False)

        self.routeBoutonListe = scrollListGen(list(routes.keys()),
                                              pygame.Rect((0, 0), (125, 17)), self.routeContainer, False)[1]

        # la liste des types avion
        self.typeAvionContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (150, 200)),
                                                                           container=self.window,
                                                                           anchors={'left': 'left',
                                                                                    'left_target': self.routeContainer},
                                                                           allow_scroll_x=False)

        self.typeAvionBoutonListe = scrollListGen(
            list(avions.keys()), pygame.Rect((0, 0), (125, 17)), self.typeAvionContainer, False)[1]

        # les divers autres boutons et champs

        self.conflitsBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 20), (200, 17)),
            text='Générateur de conflits',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.typeAvionContainer, 'left': 'left',
                     'left_target': self.routeContainer})

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
            anchors={'top': 'top', 'top_target': self.arrivalBouton, 'left': 'left',
                     'left_target': self.routeContainer})

        self.indicatiflabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer},
            text='Indicatif')

        self.indicatifinput = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((0, 0), (200, 30)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top',
                     'top_target': self.indicatiflabel})

        self.FLlabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top',
                     'top_target': self.indicatifinput},
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

        elif event.ui_element == self.conflitsBouton:
            self.returnValues['conflit'] = not self.returnValues['conflit']
            if not self.conflitsBouton.is_selected:
                self.conflitsBouton.select()
            else:
                self.conflitsBouton.unselect()

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
                if 'FL' in self.returnValues:
                    self.returnValues.update({'PFL': self.returnValues['FL']})
                else:
                    self.returnValues.update({'PFL': 310})

        # on vérifie l'indicatif
        elif event.ui_element == self.indicatifinput:
            self.returnValues.update({'indicatif': event.text})

    def kill(self):
        self.window.kill()

    def checkAlive(self):
        return self.window.alive()


class etiquette:

    def __init__(self, avion):

        clicks = frozenset([pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])

        self.extended = True  # relate de si l'étiquette est étendue ou non
        self.centre = (0, 0)

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
            text=str(round(avion.papa.altitude / 100)),
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

        self.clearedSpeed = pygame_gui.elements.UIButton(
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
        self.ligneTrois = [self.AFL, self.CFL, self.DCT, self.clearedSpeed, self.rate]
        self.ligneQuatre = [self.XPT, self.XFL, self.PFL, self.nextSector]
        self.rect = self.container.get_abs_rect()

    def update(self, avion):

        """
        On ajuste la position ainsi que les valeurs textes dans les boutons
        """

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

        if not avion.papa.clearedHeading:
            self.DCT.set_text(avion.papa.DCT)
        elif self.extended:
            self.DCT.set_text("h" + str(avion.papa.clearedHeading))
        else:
            self.DCT.set_text("h")

        self.XPT.set_text(avion.papa.XPT)
        self.nextSector.set_text(avion.papa.nextSector)

        # alti
        self.AFL.set_text(str(round(avion.papa.altitude / 100)) + " " + avion.papa.altitudeEvoTxt)

        self.CFL.set_text(str(avion.papa.CFL)[:2])

        self.PFL.set_text("p" + str(avion.papa.PFL)[:2])

        self.XFL.set_text("x" + str(avion.papa.XFL)[:2])
        if avion.papa.clearedIAS and self.extended:
            self.clearedSpeed.set_text("k" + avion.papa.clearedIAS)
        elif avion.papa.clearedMach and self.extended:
            self.clearedSpeed.set_text("k" + avion.papa.clearedMach)
        else:
            self.clearedSpeed.set_text("S")

        if avion.papa.clearedRate and self.extended:
            self.rate.set_text("r" + avion.papa.clearedRate)
        else:
            self.rate.set_text("R")

        self.boutonAgauche()  # TODO utiliser cette fonction que quand c'est nécessaire

        # container
        self.container.set_position((avion.etiquetteX, avion.etiquetteY))
        self.container.update_containing_rect_position()
        self.container.recalculate_abs_edges_rect()
        self.centre = (avion.etiquetteX + self.rect[2] / 2, avion.etiquetteY + self.rect[3] / 2)

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
        self.lastHovered = 0  # temps : la dernière fois que le menu était survolé

        width = 80
        height = 120

        x = pos[0] - width / 2
        y = pos[1] - 35

        if avion.papa.etatFrequence == 'previousFreq':
            text = 'FORCE ASSU'
        elif avion.papa.etatFrequence == 'previousShoot':
            text = 'ASSUME'
        elif avion.papa.etatFrequence == 'nextCoord':
            text = avion.papa.nextFrequency
        elif avion.papa.etatFrequence == 'nextShoot':
            text = 'RECLAIM'
        else:
            text = ''

        self.window = pygame_gui.elements.UIWindow(pygame.Rect((x, y), (width, height)),
                                                   draggable=False,
                                                   window_display_title=avion.papa.indicatif,
                                                   object_id=pygame_gui.core.ObjectID('@menu', 'blanc'))
        self.window.set_minimum_dimensions((width, width))
        self.window.set_dimensions((width, height))

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

    def checkHovered(self) -> None:
        """
        Commence le compteur si n'est plus survolé
        :return:
        """
        rect = self.window.get_abs_rect()
        mouse = pygame.mouse.get_pos()

        if rect[0] <= mouse[0] <= rect[0] + rect[2] and rect[1] <= mouse[1] <= rect[1] + rect[3]:
            self.lastHovered = pygame.time.get_ticks()

        elif pygame.time.get_ticks() - self.lastHovered > temps_disparition_menus:
            self.kill()

    def kill(self):
        self.window.kill()

    def checkAlive(self):
        self.checkHovered()
        return self.window.alive()


class menuValeurs:

    def __init__(self, avion, pos: list[float, float] | tuple[float, float], valeur: str, pilote: bool):

        """
        Menu utilisé par le controleur pour changer les valeurs des différents champs
        :param avion:
        :param pos:
        :param valeur:
        :param pilote: si on est en pilote ou non
        """

        self.avion = avion
        self.valeur = valeur
        self.lastHovered = 0  # valeur pour fermer le menu après un temps de non survol

        width = 70
        height = 240

        x = pos[0] - width / 2
        y = pos[1] - 35

        self.liste = []
        self.listeAff = []

        self.containerHdgGauche = None
        self.containerHdgDroite = None
        self.headingDCT = None
        self.listeGauche = None
        self.listeDroite = None
        objectID = None

        if valeur == 'DCT':
            self.liste = [point['name'] for point in self.avion.papa.route['points']]
            self.listeAff = self.liste[self.liste.index(avion.papa.nextPoint['name']):]
            objectID = pygame_gui.core.ObjectID('@menuLabel', 'menuBlanc')

        elif valeur == 'XPT':  # la diff de liste est qu'on ne prend pas en compte les points de notre secteur ici
            self.liste = [point['name'] for point in self.avion.papa.route['points']]
            self.listeAff = self.liste[self.liste.index(avion.papa.defaultXPT):]
            objectID = pygame_gui.core.ObjectID('@menuLabel', 'menuBlanc')

        elif valeur == 'C_IAS':
            self.liste = [*range(0, 60)]
            self.liste.reverse()
            if avion.papa.clearedIAS:
                indexDeVitesse = self.liste.index(int(avion.papa.clearedIAS[:2]))
            else:
                indexDeVitesse = self.liste.index(round(avion.papa.speedIAS / 10))
            self.listeAff = self.liste[indexDeVitesse - 4: indexDeVitesse + 5]

        elif valeur == 'C_Rate':
            self.liste = [*range(500, 6000, 500)]
            self.liste.reverse()
            self.listeAff = self.liste[-7:]

        elif valeur in ['XFL', 'PFL', 'CFL', 'FL']:
            self.liste = [*range(0, 600, 10)]
            self.liste.reverse()
            indexDuFL = self.liste.index(avion.papa.PFL)
            self.liste[indexDuFL] = "R" + str(avion.papa.PFL)
            self.listeAff = self.liste[indexDuFL - 4: indexDuFL + 5]

        elif valeur in ['HDG', 'C_HDG']:

            cap = round(avion.papa.selectedHeading // 5) * 5 + 5

            self.liste = [*range(5, 365, 5)]
            indexDuCap = self.liste.index(cap)
            self.listeAff = [self.liste[(indexDuCap - 3 + i) % len(self.liste)] for i in range(7)]
            objectID = pygame_gui.core.ObjectID('@menuLabel', 'menuBlanc')

        self.window = pygame_gui.elements.UIWindow(pygame.Rect((x, y), (width, height)),
                                                   window_display_title=valeur,
                                                   object_id=pygame_gui.core.ObjectID('@menu', 'blanc'),
                                                   draggable=False)

        self.topContainer = pygame_gui.elements.UIScrollingContainer(
            container=self.window,
            relative_rect=pygame.Rect((0, 0), (0, 0)),
            allow_scroll_y=False,
            allow_scroll_x=False)

        self.noeud = None
        self.mach = None
        self.resume = None
        self.plusBouton = None
        self.moinsBouton = None

        if valeur == 'C_IAS':
            self.noeud = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width / 2, -1)),
                container=self.topContainer,
                text="K")

            self.mach = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width / 2, -1)),
                container=self.topContainer,
                text="M",
                anchors={'left': 'left', 'left_target': self.noeud})

            self.resume = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width, -1)),
                container=self.topContainer,
                text="RESUME",
                anchors={'top': 'top', 'top_target': self.noeud})

            self.moinsBouton = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width / 2, -1)),
                container=self.topContainer,
                text="-",
                anchors={'top': 'top', 'top_target': self.resume})

            self.plusBouton = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width / 2, -1)),
                container=self.topContainer,
                text="+",
                anchors={'top': 'top', 'top_target': self.resume, 'left': 'left', 'left_target': self.moinsBouton})

            self.topContainer.set_dimensions((width, self.noeud.get_abs_rect()[3] * 3))

        elif self.valeur == 'C_Rate':

            self.resume = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width, -1)),
                container=self.topContainer,
                text="RESUME")

            self.moinsBouton = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width / 2, -1)),
                container=self.topContainer,
                text="-",
                anchors={'top': 'top', 'top_target': self.resume})

            self.plusBouton = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width / 2, -1)),
                container=self.topContainer,
                text="+",
                anchors={'top': 'top', 'top_target': self.resume, 'left': 'left', 'left_target': self.moinsBouton})

            self.topContainer.set_dimensions((width, self.moinsBouton.get_abs_rect()[3] * 2))

        elif self.valeur == 'DCT':

            self.resume = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width, -1)),
                container=self.topContainer,
                text="CONTINUE")

            self.headingDCT = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width, -1)),
                container=self.topContainer,
                text="HDG",
                anchors={'top': 'top', 'top_target': self.resume})

            self.topContainer.set_dimensions((width, self.headingDCT.get_abs_rect()[3] * 2))

        if self.valeur in ['C_HDG', 'HDG']:

            listeDroite = []
            listeGauche = []

            for i in range(5, 35, 5):
                listeDroite.append("+" + str(i))
                listeGauche.append("-" + str(i))

            listeDroite.append("+40")
            listeGauche.append("-40")

            self.resume = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width, -1)),
                container=self.topContainer,
                text="CONTINUE")

            self.headingDCT = pygame_gui.elements.UIButton(
                pygame.Rect((0, 0), (width, -1)),
                container=self.topContainer,
                text="DCT",
                anchors={'top': 'top', 'top_target': self.resume})

            self.topContainer.set_dimensions((width, self.headingDCT.get_abs_rect()[3] * 2))

            self.containerHdgGauche = pygame_gui.elements.UIScrollingContainer(
                container=self.window,
                relative_rect=pygame.Rect((0, 0), (width / 3, height)),
                allow_scroll_x=False,
                allow_scroll_y=False,
                anchors={'top': 'top', 'top_target': self.topContainer}
            )

            self.listeGauche = scrollListGen(
                listeGauche,
                pygame.Rect((1, 0), (width / 3, -1)),
                self.containerHdgGauche,
                sliderBool=False)[1]

            self.listeContainer = pygame_gui.elements.UIScrollingContainer(
                container=self.window,
                relative_rect=pygame.Rect((0, 0), (width / 3, height)),
                allow_scroll_x=False,
                allow_scroll_y=False,
                anchors={'top': 'top', 'top_target': self.topContainer,
                         'left': 'left', 'left_target': self.containerHdgGauche}
            )

            self.listeBoutons = scrollListGen(
                self.listeAff,
                pygame.Rect((1, 0), (width / 3, -1)),
                self.listeContainer,
                sliderBool=False,
                objectID=objectID)[1]

            self.containerHdgDroite = pygame_gui.elements.UIScrollingContainer(
                container=self.window,
                relative_rect=pygame.Rect((1, 0), (width / 3, height)),
                allow_scroll_x=False,
                allow_scroll_y=False,
                anchors={'top': 'top', 'top_target': self.topContainer,
                         'left': 'left', 'left_target': self.listeContainer}
            )

            self.listeDroite = scrollListGen(
                listeDroite,
                pygame.Rect((1, 0), (width / 3, -1)),
                self.containerHdgDroite,
                sliderBool=False)[1]
        else:
            self.listeContainer = pygame_gui.elements.UIScrollingContainer(
                container=self.window,
                relative_rect=pygame.Rect((0, 0), (width, height)),
                allow_scroll_x=False,
                allow_scroll_y=False,
                anchors={'top': 'top', 'top_target': self.topContainer}
            )

            tempo = scrollListGen(
                self.listeAff,
                pygame.Rect((1, 0), (width, -1)),
                self.listeContainer,
                sliderBool=False,
                objectID=objectID)

            self.listeBoutons = tempo[1]

        if valeur in ['XFL', 'PFL', 'CFL']:  # on ramène la fenêtre au bon endroit pour la souris (sur le PFL)
            y = y - (self.topContainer.get_abs_rect()[3] + self.listeBoutons[0].get_abs_rect()[
                3] * 2.5 + self.window.title_bar_height)
            self.window.set_position((x, y))

        widthListeContainer = self.listeContainer.get_abs_rect()[2]

        self.listeContainer.set_dimensions(
            (widthListeContainer, len(self.listeAff) * self.listeBoutons[0].get_abs_rect()[3]))
        self.window.set_minimum_dimensions((width, width))
        height = (self.listeContainer.get_abs_rect()[3] +
                  self.topContainer.rect[3] +
                  self.window.title_bar_height)

        self.window.set_dimensions(
            (width,
             height))

        if pilote:
            if self.valeur == 'DCT':
                self.valeur = 'Direct'
            elif self.valeur == 'C_Rate':
                self.valeur = 'Rate'
            elif self.valeur == 'C_IAS':
                self.valeur = 'IAS'
            elif self.valeur == 'C_HDG':
                self.valeur = 'HDG'

    def checkEvent(self, event):
        """
        Vérifies si un event est relié à ce menu et prend les actions en conséquence
        :param event: l'event à vérifier
        :return:
        """

        if event.ui_element in self.listeBoutons:
            self.kill()

            if self.valeur == 'C_Rate':
                event.ui_element.set_text(event.ui_element.text[:2])

            if self.valeur in ['C_IAS', 'C_Rate']:
                if self.moinsBouton.is_selected:
                    valeur = event.ui_element.text + '-'

                elif self.plusBouton.is_selected:
                    valeur = event.ui_element.text + '+'

                else:
                    valeur = event.ui_element.text

            elif event.ui_element.text[0] == 'R':  # si on a une value qui correspond au PFL, alors il faut enlever le R

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

        elif event.ui_element == self.plusBouton:
            if self.plusBouton.is_selected:
                self.plusBouton.unselect()
            else:
                self.plusBouton.select()
                self.moinsBouton.unselect()

        elif event.ui_element == self.moinsBouton:
            if self.moinsBouton.is_selected:
                self.moinsBouton.unselect()
            else:
                self.moinsBouton.select()
                self.plusBouton.unselect()

        elif event.ui_element == self.resume:
            self.kill()
            if self.valeur in ['DCT', 'C_HDG']:  # si c'est un cap, alors on veut continuer au cap
                return self.avion.Id, 'C_HDG', self.avion.papa.selectedHeading

            elif self.valeur in ['Direct', 'HDG']:
                return self.avion.Id, 'HDG', self.avion.papa.selectedHeading

            else:  # si c'est une rate ou IAS : on enlève
                return self.avion.Id, self.valeur, None

        elif event.ui_element == self.headingDCT:
            self.kill()
            if self.valeur in ['C_HDG', 'HDG']:
                return 'DCT'
            else:
                return 'C_HDG'

        elif self.valeur in ['C_HDG', 'HDG']:
            if event.ui_element in self.listeGauche:
                self.kill()
                if self.avion.papa.clearedHeading:
                    heading = round(self.avion.papa.clearedHeading - int(event.ui_element.text[1:]))
                else:
                    heading = round(self.avion.papa.selectedHeading - int(event.ui_element.text[1:]))
                return self.avion.Id, self.valeur, heading

            elif event.ui_element in self.listeDroite:
                self.kill()
                if self.avion.papa.clearedHeading:
                    heading = round(self.avion.papa.clearedHeading + int(event.ui_element.text[1:]))
                else:
                    heading = round(self.avion.papa.selectedHeading + int(event.ui_element.text[1:]))
                return self.avion.Id, self.valeur, heading

    def checkScrolled(self, event):
        """
        Vérifie si le menu est en train d'être scrollé
        :return:
        """

        mouse = pygame.mouse.get_pos()
        rect = self.window.get_abs_rect()

        if not rect[0] <= mouse[0] <= rect[0] + rect[2] and rect[1] <= mouse[1] <= rect[1] + rect[3]:
            return True

        indexDebut = self.liste.index(self.listeAff[0])

        if event.y >= 0:  # on regarde dans quel sens on scroll
            newIndex = (indexDebut - 1) % len(self.liste)
        else:
            newIndex = (indexDebut + 1) % len(self.liste)

        self.listeAff = [self.liste[(newIndex + i) % len(self.liste)] for i in range(len(self.listeAff))]

        self.scrollUpdate()

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
                dessin = False
                for element in self.listeBoutons:
                    if element.hovered:
                        dessin = True
                        break
                if not dessin:
                    self.avion.pointDessinDirect = None

    def checkMenuHovered(self) -> None:
        """
        Commence le compteur si n'est plus survolé
        :return:
        """
        rect = self.window.get_abs_rect()
        mouse = pygame.mouse.get_pos()

        if rect[0] <= mouse[0] <= rect[0] + rect[2] and rect[1] <= mouse[1] <= rect[1] + rect[3]:
            self.lastHovered = pygame.time.get_ticks()

        elif pygame.time.get_ticks() - self.lastHovered > temps_disparition_menus:
            self.kill()

    def kill(self):
        self.window.kill()
        self.avion.pointDessinDirect = None

    def checkAlive(self):
        self.checkMenuHovered()
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
                + ' ' + str(round(avion.papa.altitude / 100)) + ' ' + str(avion.papa.PFL)
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


class menuRadar:

    def __init__(self):

        width = 100
        height = 200

        self.window = pygame_gui.elements.UIWindow(
            pygame.Rect((500, 500), (width, height)),
            window_display_title="Flight Data Window",
            object_id=pygame_gui.core.ObjectID('@menuRadar', 'blanc'),

        )
        ancres = {}
        self.listeVecteurs = []
        indice = 0

        for b in range(3):

            for bb in range(3):
                indice += 1
                self.listeVecteurs.append(
                    pygame_gui.elements.UIButton(pygame.Rect((0, 0), (width / 3, width / 3)),
                                                 text=str(indice) + "'",
                                                 container=self.window,
                                                 anchors=ancres,
                                                 object_id=pygame_gui.core.ObjectID('@menuRadar', 'blanc'),
                                                 generate_click_events_from=frozenset(
                                                     [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT])
                                                 ))
                ancres.update({'left': 'left', 'left_target': self.listeVecteurs[-1]})
            ancres.pop('left')
            ancres.pop('left_target')
            ancres.update({'top': 'top', 'top_target': self.listeVecteurs[-1]})

        self.alidade = pygame_gui.elements.UIButton(pygame.Rect((0, 0), (width, width / 3)),
                                                   text="ALIDADE",
                                                   container=self.window,
                                                   anchors={'top': 'top', 'top_target': self.listeVecteurs[-1]},
                                                   object_id=pygame_gui.core.ObjectID('@menuRadar', 'blanc'))

        self.cercles = pygame_gui.elements.UIButton(pygame.Rect((0, 0), (width, width / 3)),
                                                   text="@",
                                                   container=self.window,
                                                   anchors={'top': 'top', 'top_target': self.alidade},
                                                   object_id=pygame_gui.core.ObjectID('@menuRadar', 'blanc'))

        ancres = {'top': 'top', 'top_target': self.cercles}
        self.listeSep = []
        for lettre in ['A', 'B', 'C']:
            self.listeSep.append(
                pygame_gui.elements.UIButton(pygame.Rect((0, 0), (width / 3, width / 3)),
                                             text=lettre,
                                             container=self.window,
                                             anchors=ancres,
                                             object_id=pygame_gui.core.ObjectID('@menuRadar', 'blanc')
                                             ))
            ancres.update({'left': 'left', 'left_target': self.listeSep[-1]})

        self.lastHovered = pygame.time.get_ticks()
        self.window.hide()

    def show(self):

        pos = pygame.mouse.get_pos()
        rect = self.window.get_abs_rect()
        self.window.set_position((pos[0] - rect[2] / 2, pos[1] - rect[3] / 2))
        self.window.show()

    def checkActive(self):
        return self.window.visible

    def checkEvent(self, event):

        if event.ui_element in self.listeVecteurs:
            if event.mouse_button == 1:
                return 'VecteursToggle', int(event.ui_element.text[0])

            elif event.mouse_button == 3:
                return 'Vecteurs', int(event.ui_element.text[0])

        elif event.ui_element in self.listeSep:
            self.window.hide()
            return 'Sep', event.ui_element.text

        elif event.ui_element == self.alidade:
            self.window.hide()
            return 'Alidade'

        elif event.ui_element == self.cercles:
            self.window.hide()
            return 'Cercles'

    def checkMenuHovered(self) -> None:
        """
        Commence le compteur si n'est plus survolé
        :return:
        """
        rect = self.window.get_abs_rect()
        mouse = pygame.mouse.get_pos()

        if rect[0] <= mouse[0] <= rect[0] + rect[2] and rect[1] <= mouse[1] <= rect[1] + rect[3]:
            self.lastHovered = pygame.time.get_ticks()

        elif pygame.time.get_ticks() - self.lastHovered > temps_disparition_menus:
            self.window.hide()

