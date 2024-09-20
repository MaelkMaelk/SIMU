from typing import Iterable
import pygame
import math
import pygame_gui

import geometry
import interface

plotSize = 6
radarRefresh = 4
timeConstant = radarRefresh / 3600
listeEtrangers = ['G2', 'M2']
etiquetteLines = 4
nmToFeet = 6076
axe = 74
axePoint = 'BST'


def positionAffichage(x, y, zoom, scrollX, scrollY):  # TODO rassembler x, y en (x,y) pareil pour le scroll
    """
    :param x: position en x
    :param y: position en y
    :param zoom: coefficient d'élargissement des distances
    :param scrollX: décalage en x
    :param scrollY: décalage en y
    :return: x, y pour l'affichage
    """

    x = x * zoom + scrollX
    y = y * zoom + scrollY
    return x, y


def positionBrute(position, zoom, scroll):  # TODO remplacer les endroits ou on utilise pas la fonction
    """
    Transforme une position graphique en une position sur la gameMap
    :param position: vecteur2 (x, y)
    :param zoom: scalaire de zoom
    :param scroll: vecteur2 (scrollx, scrolly)
    :return: x, y
    """


class Avion:

    global timeConstant
    global plotSize

    def __init__(self, Id, papa):
        self.Id = Id
        self.papa = papa
        self.bouton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.papa.x, self.papa.y), (plotSize * 2, plotSize * 2)), text='')
        self.bouton.generate_click_events_from: Iterable[int] = frozenset(
            [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])

        # Radar display
        self.visible = True
        self.predictionPoint = None  # point pour la prédiction de route
        self.drawRouteBool = False
        self.locWarning = False
        self.etiquetteExtended = False
        self.unHoverTime = pygame.time.get_ticks()

        # etiquette
        self.etiquetteX = papa.x + 60
        self.etiquetteY = papa.y - 60
        self.etiquettePos = 0

        # Zoom & scroll
        self.affX = 0
        self.affY = 0

        # init de l'étiquette
        self.etiquette = interface.etiquette(self)

        # interaction avec les events
        self.returnValues = {}

    def positionEtiquette(self):
        """On place l'étiquette dans une des positions possibles (nord est, NO, SE, SO)"""

        value = 45  # distance de l'etiquette par rapport au plot
        if self.etiquettePos % 4 == 0:
            self.etiquetteX = self.affX + plotSize + value
            self.etiquetteY = self.affY + plotSize - value
        elif self.etiquettePos % 4 == 1:
            self.etiquetteX = self.affX + plotSize + value
            self.etiquetteY = self.affY + plotSize + value
        elif self.etiquettePos % 4 == 2:
            self.etiquetteX = self.affX + plotSize - value
            self.etiquetteY = self.affY + plotSize + value
        else:
            self.etiquetteX = self.affX + plotSize - value
            self.etiquetteY = self.affY + plotSize - value

    def drawVector(self, color, window, vecteurSetting, zoom):
        """

        :param color: quelle couleur pour le vecteur ?
        :param window: quelle surface ? (mettre la surface qu'on utilise pour pygame)
        :param vecteurSetting: int à combien de minutes on doit les dessiner
        :param zoom: niveau de zoom de la fenêtre
        :return: rien
        """
        for i in range(1, vecteurSetting + 1):

            pygame.draw.line(window, color, (self.affX + plotSize, self.affY + plotSize), (
                self.affX + plotSize + self.papa.speedPx * 60 / radarRefresh * vecteurSetting * zoom * math.cos(
                    self.papa.headingRad),
                self.affY + plotSize + self.papa.speedPx * 60 / radarRefresh * vecteurSetting * zoom * math.sin(
                    self.papa.headingRad)), 1)

            pygame.draw.circle(window, color, (self.affX + plotSize +
                                            self.papa.speedPx * 60 / radarRefresh * i * zoom * math.cos(
                self.papa.headingRad),
                                            self.affY + plotSize +
                                            self.papa.speedPx * 60 / radarRefresh * i * zoom * math.sin(
                                                self.papa.headingRad)),
                               2)

    def draw(self, win, zoom, scroll, vecteurs, vecteurSetting, points):

        # updates

        # ces coordonées correspondent au sommet haut gauche du plot avion
        self.affX = self.papa.x * zoom - plotSize + scroll[0]
        self.affY = self.papa.y * zoom - plotSize + scroll[1]

        self.bouton.set_position((self.affX, self.affY))

        if self.drawRouteBool:
            self.drawRoute(points, win, zoom, scroll)

        self.positionEtiquette()  # on détermine la position de l'étiquette (nord est, SE, NO, SO)
        self.checkEcheckEtiquetteOnUnhover()
        self.extendEtiquette()
        self.etiquette.update(self)  # on update via la fonction de l'étiquette



        # Dessin
        if self.visible:
            if self.papa.warning:
                color = (255, 120, 60)
            elif self.locWarning:
                color = (100, 200, 100)
            elif self.papa.part:
                color = (30, 144, 255)
            else:
                color = (255, 255, 255)

            pygame.draw.circle(win, (255, 255, 255), (self.affX + plotSize, self.affY + plotSize), plotSize, 1)

            if vecteurs or self.papa.warning or self.locWarning:  # si on doit dessiner les vecteurs
                self.drawVector(color, win, vecteurSetting, zoom)  # on appelle la fonction

            radius = 1
            for plot in self.papa.comete:
                affPlot = [plot[0] * zoom + scroll[0],
                           plot[1] * zoom + scroll[1]]
                pygame.draw.circle(win, (255, 255, 255), affPlot, int(round(radius)), 1)
                radius += 0.7
            pygame.draw.line(win, (255, 255, 255), (self.affX + plotSize, self.affY + plotSize),
                             (self.etiquetteX, self.etiquetteY))

    def drawEstimatedRoute(self, points, temps, win, zoom, scroll):
        """
        Dessine la route future de l'avion jusuq'à un certain point défini par une valeur de temps
        C'est une bonne approximation de la future position de l'avion, à vitesse constante
        :param points: la liste des points récupérer les coords
        :param temps: combien de temps doit faire la route dessinée
        :param win: l'écran pygame
        :param zoom: le niveau de zoom
        :param scroll: le scroll format [x, y]
        :return:
        """

        route = self.papa.route['points']  # on n'a besoin que des noms des points
        nextPoint = self.papa.nextPoint
        ratio = 0

        route = route[route.index(nextPoint):]  # on ne considère que la route devant l'avion
        pointUn = [self.papa.x, self.papa.y]  # on commence à dessiner à partir de l'avion
        distance = temps * self.papa.speedPx  # on établit la distance de la route avec notre vitesse

        for point in route:
            pointDeux = [points[point['name']][0], points[point['name']][1]]

            # on calcule la distance de la branche
            legDistance = geometry.calculateDistance(pointUn[0], pointUn[1], pointDeux[0], pointDeux[1])

            if legDistance > distance:  # si le trajet restant est plus petit que la prochaine branche
                ratio = distance/legDistance  # on regarde le pourcentage de recouvrement

                # on détermine le point final du dessin avec ce ratio
                pointDeux = [pointUn[0] + (pointDeux[0] - pointUn[0]) * ratio,
                             pointUn[1] + (pointDeux[1] - pointUn[1]) * ratio]

                # on dessine alors la dernière branche
                pygame.draw.line(win, (0, 255, 0),
                                 (pointUn[0] * zoom + scroll[0], pointUn[1] * zoom + scroll[1]),
                                 (pointDeux[0] * zoom + scroll[0], pointDeux[1] * zoom + scroll[1]))

                self.predictionPoint = pointDeux

                break  # on casse la boucle for, pas la peine de faire des calculs pour plus loin, la prédi est finie

            else:  # si le trajet s'arrête après la branche, on dessine la branche en entier
                pygame.draw.line(win, (0, 255, 0),  # TODO changer avec la fct positionAffichage
                                 (pointUn[0] * zoom + scroll[0], pointUn[1] * zoom + scroll[1]),
                                 (pointDeux[0] * zoom + scroll[0], pointDeux[1] * zoom + scroll[1]))

            distance -= legDistance  # on enlève la distance de la branche parcourue à la distance à parcourir
            pointUn = pointDeux  # on passe au prochain point

    def drawRoute(self, points, win, zoom, scroll):
        """
        Dessine la route future de l'avion avec les estimées en temps
        :param points: la liste des points récupérer les coords
        :param win: l'écran pygame
        :param zoom: le niveau de zoom
        :param scroll: le scroll format [x, y]
        :return:
        """

        route = self.papa.route['points']  # on n'a besoin que des noms des points
        nextPoint = self.papa.nextPoint
        ratio = 0

        point1 = points[route[route.index(nextPoint) - 1]['name']][:2]
        point2 = points[nextPoint['name']][:2]
        pointUn = geometry.calculateShortestPoint(point1, point2, [self.papa.x, self.papa.y])
        # TODO heure de passage pour chaque point
        route = route[route.index(nextPoint):]  # on ne considère que la route devant l'avion

        for point in route:
            pointDeux = [points[point['name']][0], points[point['name']][1]]

            pygame.draw.line(win, (25, 25, 170),  # TODO changer avec la fct positionAffichage
                             (pointUn[0] * zoom + scroll[0], pointUn[1] * zoom + scroll[1]),
                             (pointDeux[0] * zoom + scroll[0], pointDeux[1] * zoom + scroll[1]), 2)

            pointUn = pointDeux  # on passe au prochain point

    def checkEvent(self, event, pilote):

        """
        Vérifie si un bouton associé à l'avion correspond à l'event
        :param event: événement à vérifier
        :param pilote: si l'interface est en mode pilote ou non
        :return:
        """

        if event.ui_element == self.bouton:
            if event.mouse_button == 2 and not pilote:  # clic milieu
                return self.Id, 'Warning'

            elif event.mouse_button == 1:  # clic gauche
                self.etiquettePos += 1

            elif event.mouse_button == 3:
                if pilote:  # si on est en pilote alors ça supp l'avion
                    return self.Id, 'Remove'
                self.locWarning = not self.locWarning  # toggle les warnings locs

        elif event.ui_element == self.etiquette.indicatif:
            if event.mouse_button == 1 and pilote:
                return 'menu'

        elif event.ui_element == self.etiquette.XPT:
            if event.mouse_button == 1 and not pilote:
                self.drawRouteBool = not self.drawRouteBool

    def checkEtiquetteOnHover(self):
        """
        Vérifie si on doit ou non étendre l'étiquette
        :return: True si l'event appartient à cette étiquette
        """

        if self.etiquette.container.are_contents_hovered():
            self.etiquetteExtended = True
            return True
        return False

    def checkEcheckEtiquetteOnUnhover(self):

        """
        Vérifie si on doit ou non désétendre l'étiquette
        """

        if self.etiquette.container.are_contents_hovered():
            self.unHoverTime = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - self.unHoverTime > 400:
            self.etiquetteExtended = False

    def extendEtiquette(self):
        """
        Étend ou range l'étiquette
        """

        if self.etiquetteExtended and not self.etiquette.extended:  # si on doit etendre et elle n'est pas étendue
            self.etiquette.extended = True

            for ligne in [self.etiquette.ligneDeux, self.etiquette.ligneTrois, self.etiquette.ligneQuatre]:
                for bouton in ligne:
                    bouton.show()

        elif self.etiquette.extended and not self.etiquetteExtended:  # si on doit rentrer et elle est étendue
            self.etiquette.extended = False

            self.etiquette.type_dest.hide()
            self.etiquette.DCT.hide()

            self.etiquette.speedIAS.hide()  # TODO faire en sorte qu'ils ne se cache pas en -h ou -r
            self.etiquette.rate.hide()
            self.etiquette.nextSector.hide()

            self.etiquette.XFL.hide()  # TODO faire en sorte qu'ils ne se cache pas si les FL sont pas pareils
            self.etiquette.CFL.hide()

    def update(self, papa):
        self.papa = papa

    def kill(self):
        self.bouton.kill()
        self.etiquette.kill()


class MenuATC:

    def __init__(self, Idtuple, x, y):
        self.Idtuple = Idtuple
        self.window = pygame_gui.elements.UIWindow(pygame.Rect((x, y), (100, 250)))

        self.partBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='PART',
            container=self.window)

        self.movBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='MVT',
            container=self.window, anchors={'top': 'top', 'top_target': self.partBouton})

        self.FLBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='FL?',
            container=self.window, anchors={'top': 'top', 'top_target': self.movBouton})

        self.montrerBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='Montrer',
            container=self.window, anchors={'top': 'top', 'top_target': self.FLBouton})

    def kill(self):
        self.window.kill()
        return self.Idtuple

