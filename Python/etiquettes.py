
# Module Imports

import pygame_gui
import pygame


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


class etiquette:

    def __init__(self, avion):

        clicks = frozenset([pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])

        self.extended = True  # relate de si l'étiquette est étendue ou non
        self.downlink = False
        self.centre = (0, 0)

        if avion.papa.CPDLC:
            indicatifText = avion.papa.indicatif + ' ϟ'
        else:
            indicatifText = avion.papa.indicatif

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
            text=indicatifText,
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

        self.selectedHeading = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=str(round(avion.papa.selectedHeading)),
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.selectedAlti = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text=avion.papa.nextSector,
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.selectedSpeed = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, -1)),
            text="45",
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquette', 'rose'),
            anchors={'top': 'top', 'top_target': self.AFL},
            container=self.container)

        self.ligneDeux = [self.indicatif, self.type_dest]
        self.ligneTrois = [self.AFL, self.CFL, self.DCT, self.clearedSpeed, self.rate]
        self.ligneQuatre = [self.XPT, self.XFL, self.PFL, self.nextSector]
        self.ligneCinq = [self.selectedHeading, self.selectedAlti, self.selectedSpeed]
        self.rect = self.container.get_abs_rect()
        self.surlignageLoc = [self.type_dest, self.CFL, self.PFL, self.nextSector]
        self.surlignagePos = [self.indicatif, self.XPT, self.XFL, self.selectedHeading, self.selectedAlti, self.selectedSpeed]

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

        # vitesse
        if avion.papa.clearedIAS and self.extended:
            self.clearedSpeed.set_text("k" + avion.papa.clearedIAS)
        elif avion.papa.clearedMach and self.extended:
            self.clearedSpeed.set_text("m" + avion.papa.clearedMach)
        else:
            self.clearedSpeed.set_text("S")

        if avion.papa.clearedRate and self.extended:
            self.rate.set_text("r" + avion.papa.clearedRate)
        else:
            self.rate.set_text("R")

        # paramètres descendants
        if avion.papa.machMode:
            self.selectedSpeed.set_text("@" + str(round(avion.papa.selectedMach, 2)))
        else:
            self.selectedSpeed.set_text("@k" + str(round(avion.papa.selectedIAS)))

        self.selectedHeading.set_text("@h" + str(round(avion.papa.selectedHeading)))
        self.selectedAlti.set_text("@" + str(avion.papa.selectedAlti)[:2])

        self.boutonAgauche()

        # container
        self.container.set_position((avion.etiquetteX, avion.etiquetteY))
        self.container.update_containing_rect_position()
        self.container.recalculate_abs_edges_rect()
        self.centre = (avion.etiquetteX + self.rect[2] / 2, avion.etiquetteY + self.rect[3] / 2)

    def boutonAgauche(self):

        """
        Méthode qui met les boutons le plus à gauche possible de l'étiquette en fonction des boutons visibles
        """

        for ligne in [self.ligneDeux, self.ligneTrois, self.ligneQuatre, self.ligneCinq]:  # on fait pour chaque ligne
            for numBouton in range(len(ligne)):  # on fait avec un range pour pouvoir tronquer la liste

                bouton = ligne[numBouton]  # on récupère le bouton
                if bouton.visible:
                    distance = updateDistanceGauche(ligne[:numBouton])
                    if bouton in self.ligneCinq:
                        y = bouton.get_abs_rect()[3]
                    else:
                        y = 0
                else:
                    distance = 0
                    y = 0
                bouton.set_relative_position((distance, y))

    def kill(self):
        self.container.kill()

