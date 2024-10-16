
# Native imports
import math

# Module imports
import pygame
import pygame_gui

# Imports fichiers
from Python.valeurs_config import *
import Python.geometry as geometry
import Python.interface as interface
import Python.horloge as horloge


def positionAffichage(x: int, y: int, zoom: float, scrollX: float, scrollY: float):
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


def etatFrequenceInit(avion) -> None:

    """
    Colore les boutons en fonction de l'état freq initial. À utiliser pour l'initialisation, car elle
     n'incrémente pas sur l'état précédent, mais par de 0
    :param avion: L'avion auquel est associée cette etiquette
    :return:
    """

    if avion.papa.etatFrequence != 'previousFreq':
        for etat in liste_etat_freq[:liste_etat_freq.index(avion.papa.etatFrequence) + 1]:
            avion.updateEtatFrequence(etat)


class Avion:

    global timeConstant
    global plotSize

    def __init__(self, Id: int, papa, zoom: float, scroll: list[float, float]):
        self.Id = Id
        self.papa = papa
        clicks = frozenset([pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])
        self.bouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.papa.x, self.papa.y), (plotSize * 2, plotSize * 2)),
            text='',
            generate_click_events_from=clicks,
            object_id=pygame_gui.core.ObjectID('@etiquette', 'defaults'))

        # Radar display
        self.visible = True
        self.boldXFL = True
        self.boldXPT = True
        self.predictionPoint = None  # point pour la prédiction de route
        self.drawRouteBool = False
        self.locWarning = False
        self.sep = False
        self.couleurSTCA = 'rouge'
        self.temps_cligno_stca = 0
        self.sepSetting = {}  # [temps à dessiner, distance minie en nm]
        self.etiquetteExtended = False
        self.lastHoveredTime = 0
        self.pointDessinDirect = None
        self.conflitSelected = False
        self.drag = False  # if true l'etiquette se fait drag
        self.dragOffset = (0, 0)  # le décalage de l'etiquette par rapport au curseur
        self.startPressTime = 0

        # zoom et scroll
        self.affX = self.papa.x * zoom - plotSize + scroll[0]
        self.affY = self.papa.y * zoom - plotSize + scroll[1]

        # etiquette
        self.etiquetteX = self.affX + offsettEtiquetteDefault
        self.etiquetteY = self.affY + offsettEtiquetteDefault
        self.etiquetteOffsetX = offsettEtiquetteDefault
        self.etiquetteOffsetY = offsettEtiquetteDefault

        # init de l'étiquette
        self.etiquette = interface.etiquette(self)
        etatFrequenceInit(self)
        self.checkHighlight(papa)

        # interaction avec les events
        self.returnValues = {}

    def positionEtiquette(self) -> None:
        """Met à jour la position de l'étiquette"""

        self.etiquetteX = self.affX + self.etiquetteOffsetX
        self.etiquetteY = self.affY + self.etiquetteOffsetY

    def drawVector(self, color, window, vecteurSetting, zoom):
        """

        :param color: quelle couleur pour le vecteur ?
        :param window: quelle surface ? (mettre la surface qu'on utilise pour pygame)
        :param vecteurSetting: int à combien de minutes, on doit les dessiner
        :param zoom: niveau de zoom de la fenêtre
        :return: rien
        """

        pygame.draw.line(window, color, (self.affX + plotSize, self.affY + plotSize), (
            self.affX + plotSize + self.papa.speedPx * 60 / radarRefresh * vecteurSetting * zoom * math.cos(
                self.papa.headingRad),
            self.affY + plotSize + self.papa.speedPx * 60 / radarRefresh * vecteurSetting * zoom * math.sin(
                self.papa.headingRad)), 2)

    def drawSep(self, window, zoom):
        """
        Dessine la sep avec un autre avion
        :param window:
        :param zoom:
        :return:
        """

        sep = (0, 9999999)

        for lettre, sepSetting in self.sepSetting.items():
            if sepSetting[1] <= sep[1] and 0 <= sepSetting[0]:
                sep = sepSetting

        sepSetting = sep

        coords = [self.affX + plotSize + self.papa.speedPx / radarRefresh * sepSetting[0] * zoom * math.cos(
                self.papa.headingRad),
                  self.affY + plotSize + self.papa.speedPx / radarRefresh * sepSetting[0] * zoom * math.sin(
                      self.papa.headingRad)
                  ]

        if sepSetting[1] <= 6:
            color = (255, 0, 0)
        elif sepSetting[1] <= 9:
            color = (241, 237, 57)
        else:
            color = (157, 193, 126)

        pygame.draw.line(window, color, (self.affX + plotSize, self.affY + plotSize), coords, 2)

        font = pygame.font.SysFont('arial', 15)

        coords[0] += 2
        for lettre, sepSetting in self.sepSetting.items():
            if 0 <= sepSetting[0]:
                img = font.render(lettre + str(round(sepSetting[1], 1)), True, color)
                window.blit(img, coords)
                coords[1] += 15
            else:
                img = font.render(lettre, True, (170, 170, 255))
                window.blit(img, coords)

    def drawSTCA(self):
        gras = self.etiquette.indicatif.get_object_ids()[1]
        if self.papa.STCA:
            couleur = self.couleurSTCA
            if self.couleurSTCA == 'jaune' and pygame.time.get_ticks() >= self.temps_cligno_stca + 500:
                couleur = 'rouge'
                self.temps_cligno_stca = pygame.time.get_ticks()
            elif pygame.time.get_ticks() >= self.temps_cligno_stca + 500:
                couleur = 'jaune'
                self.temps_cligno_stca = pygame.time.get_ticks()
            self.couleurSTCA = couleur
        else:

            if self.papa.etatFrequence == "previousFreq":
                couleur = 'rose'
            elif self.papa.etatFrequence in ['previousShoot', 'inFreq', 'nextCoord']:
                couleur = 'blanc'
            else:
                couleur = 'marron'
        self.etiquette.indicatif.change_object_id(pygame_gui.core.ObjectID(gras, couleur))

    def draw(self, win, zoom, scroll, vecteurs, vecteurSetting, points, temps):

        # updates

        # ces coordonées correspondent au sommet haut gauche du plot avion
        self.affX = self.papa.x * zoom - plotSize + scroll[0]
        self.affY = self.papa.y * zoom - plotSize + scroll[1]

        self.bouton.set_position((self.affX, self.affY))

        if self.drawRouteBool:
            self.drawRoute(points, win, zoom, scroll, temps)

        if self.pointDessinDirect:
            self.drawDirect(points, self.pointDessinDirect, win, zoom, scroll)

        if (self.startPressTime != 0 and self.startPressTime + dragDelay <= pygame.time.get_ticks()
                and pygame.mouse.get_pressed()[0]):
            self.etiquetteDrag()
            self.drag = True
        elif not pygame.mouse.get_pressed()[0]:  # si le bouton n'est plus pressé entre temps alors on drag pas
            self.startPressTime = 0

        self.positionEtiquette()
        if self.etiquetteExtended:
            self.checkStillHovered()
        self.extendEtiquette()
        self.etiquette.update(self)  # on update via la fonction de l'étiquette
        width = 1

        self.drawSTCA()

        # Dessin
        if not self.visible:
            return None

        if self.papa.warning:
            color = (255, 120, 60)
        elif self.locWarning:
            color = (100, 200, 100)
        elif self.etiquetteExtended:
            color = (30, 144, 255)
            width = 3
        else:
            color = (255, 255, 255)

        pygame.draw.circle(win, color, (self.affX + plotSize, self.affY + plotSize), plotSize, 1)
        pygame.draw.circle(win, color, (self.affX + plotSize, self.affY + plotSize), plotSize / 1.5, 1)

        if self.sep:
            self.drawSep(win, zoom)

        elif vecteurs or self.papa.warning or self.locWarning:  # si on doit dessiner les vecteurs
            self.drawVector(color, win, vecteurSetting, zoom)  # on appelle la fonction

        radius = 1
        for plot in self.papa.comete:
            affPlot = [plot[0] * zoom + scroll[0],
                       plot[1] * zoom + scroll[1]]
            pygame.draw.circle(win, (255, 255, 255), affPlot, int(round(radius)), 1)
            radius += 0.3

        point = self.findEtiquetteAnchorPoint()
        if point is not None:
            pygame.draw.line(win, color, (self.affX + plotSize, self.affY + plotSize),
                             (point[0], point[1]), width)

    def findEtiquetteAnchorPoint(self) -> tuple[float, float]:
        """
        Trouve le point sur le périmètre de l'étiquette pour la relier avec la tête de chaine'
        :return: Le point en question s'il est trouvé
        """
        rect = self.etiquette.container.get_abs_rect()

        pointHaut = geometry.calculateIntersection((rect[0], rect[1]),
                                                   (rect[0] + rect[2], rect[1]),
                                                   (self.etiquette.centre[0], self.etiquette.centre[1]),
                                                   (self.affX + plotSize, self.affY + plotSize))

        pointGauche = geometry.calculateIntersection((rect[0], rect[1]),
                                                     (rect[0], rect[1] + rect[3]),
                                                     (self.etiquette.centre[0], self.etiquette.centre[1]),
                                                     (self.affX + plotSize, self.affY + plotSize))

        pointDroite = geometry.calculateIntersection((rect[0] + rect[2], rect[1]),
                                                     (rect[0] + rect[2], rect[1] + rect[3]),
                                                     (self.etiquette.centre[0], self.etiquette.centre[1]),
                                                     (self.affX + plotSize, self.affY + plotSize))

        pointBas = geometry.calculateIntersection((rect[0], rect[1] + rect[3]),
                                                  (rect[0] + rect[2], rect[1] + rect[3]),
                                                  (self.etiquette.centre[0], self.etiquette.centre[1]),
                                                  (self.affX + plotSize, self.affY + plotSize))

        if rect[0] <= pointHaut[0] <= rect[0] + rect[2] and self.affY <= self.etiquetteY:
            return pointHaut
        elif rect[0] <= pointBas[0] <= rect[0] + rect[2] and self.affY >= self.etiquetteY:
            return pointBas
        elif rect[1] <= pointGauche[1] <= rect[1] + rect[3] and self.affX <= self.etiquetteX:
            return pointGauche
        elif rect[1] <= pointDroite[1] <= rect[1] + rect[3] and self.affX >= self.etiquetteX:
            return pointDroite

    def drawDirect(self, points, point, win, zoom: float, scroll: list[float, float]):
        """

        :param points: liste des points de la carte pour récup les coors
        :param point: le point avec lequel on veut une directe
        :param win: fenêtre pygame
        :param zoom: zoom
        :param scroll: scroll (x, y)
        :return:
        """

        coord = [points[point][0] * zoom + scroll[0], points[point][1] * zoom + scroll[1]]
        pygame.draw.line(win, (0, 206, 209), (self.affX + plotSize, self.affY + plotSize), coord)

    def drawEstimatedRoute(self, points, temps, color, win, zoom, scroll):
        """
        Dessine la route future de l'avion jusuq'à un certain point défini par une valeur de temps
        C'est une bonne approximation de la future position de l'avion, à vitesse constante
        :param points: la liste des points récupérer les coords
        :param temps: combien de temps doit faire la route dessinée en sec
        :param color: La couleur du tracé
        :param win: l'écran pygame
        :param zoom: le niveau de zoom
        :param scroll: le scroll format [x, y]
        :return:
        """

        if not self.conflitSelected:
            return None

        route = self.papa.route['points']  # on n'a besoin que des noms des points
        nextPoint = self.papa.nextPoint
        ratio = 0

        route = route[route.index(nextPoint):]  # on ne considère que la route devant l'avion
        pointUn = [self.papa.x, self.papa.y]  # on commence à dessiner à partir de l'avion
        distance = temps * self.papa.speedPx / radarRefresh  # on établit la distance de la route avec notre vitesse

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
                pygame.draw.line(win, color,
                                 (pointUn[0] * zoom + scroll[0], pointUn[1] * zoom + scroll[1]),
                                 (pointDeux[0] * zoom + scroll[0], pointDeux[1] * zoom + scroll[1]), 2)

                self.predictionPoint = pointDeux

                break  # on casse la boucle for, pas la peine de faire des calculs pour plus loin, la prédi est finie

            else:  # si le trajet s'arrête après la branche, on dessine la branche en entier
                pygame.draw.line(win, color,
                                 (pointUn[0] * zoom + scroll[0], pointUn[1] * zoom + scroll[1]),
                                 (pointDeux[0] * zoom + scroll[0], pointDeux[1] * zoom + scroll[1]), 2)

            distance -= legDistance  # on enlève la distance de la branche parcourue à la distance à parcourir
            pointUn = pointDeux  # on passe au prochain point

    def drawRoute(self, points: dict, win, zoom: float, scroll: tuple[float, float] | list[float, float], temps: float):
        """
        Dessine la route future de l'avion avec les estimées en temps
        :param points: la liste des points récupérer les coords
        :param win: l'écran pygame
        :param zoom: le niveau de zoom
        :param scroll: le scroll format [x, y]
        :param temps: l'heure de la partie
        :return:
        """

        route = self.papa.route['points']  # on n'a besoin que des noms des points
        nextPoint = geometry.findClosestSegment(route, (self.papa.x, self.papa.y), points)[1]

        point1 = points[route[route.index(nextPoint) - 1]['name']][:2]
        point2 = points[nextPoint['name']][:2]
        pointUn = geometry.calculateShortestPoint(point1, point2, [self.papa.x, self.papa.y])
        route = route[route.index(nextPoint):]  # on ne considère que la route devant l'avion

        font = pygame.font.SysFont('arial', 15)

        for point in route:

            pointDeux = [points[point['name']][0], points[point['name']][1]]
            temps += geometry.calculateDistance(pointUn[0], pointUn[1], pointDeux[0], pointDeux[1]) / self.papa.speedPx * radarRefresh

            pygame.draw.line(win, (46, 80, 174),
                             (pointUn[0] * zoom + scroll[0], pointUn[1] * zoom + scroll[1]),
                             (pointDeux[0] * zoom + scroll[0], pointDeux[1] * zoom + scroll[1]), 3)

            img = font.render(horloge.affichageHeure(temps), True, (70, 140, 240))
            coords = (pointDeux[0] * zoom - 5 + scroll[0], pointDeux[1] * zoom - 20 + scroll[1])
            win.blit(img, coords)

            pointUn = pointDeux  # on passe au prochain point

    def checkClicked(self, event) -> bool:
        """
        Renvoies True si un des boutons (avion ou etiquette) correspond à cet event
        :param event:
        :return:
        """
        if event.ui_element == self.bouton:
            return True
        if event.ui_element.ui_container == self.etiquette.container:
            return True
        else:
            return False

    def checkScrolled(self, event):

        if self.etiquette.extended:
            if event.y <= 0:
                self.etiquette.downlink = True
            else:
                self.etiquette.downlink = False
            return True

    def checkEvent(self, event, pilote, conflitBool):

        """
        Vérifie si un bouton associé à l'avion correspond à l'event
        :param conflitBool: Si ou non, on est en mode création de conflits
        :param event: événement à vérifier
        :param pilote: si l'interface est en mode pilote ou non
        :return:
        """

        # on vérifie que le bouton est bien associé à l'etiquette
        if event.ui_element.ui_container == self.etiquette.container:

            self.startPressTime = 0
            if self.drag:
                self.drag = False
                return None  # comme on était en train de drag, on ne fait aucune action liée au bouton

            if conflitBool:
                self.conflitSelected = not self.conflitSelected
                return None

            if event.mouse_button == 2 and not pilote:
                # si c'est un clic milieu, alors on surligne ou non le bouton

                if event.ui_element in self.etiquette.surlignagePos:
                    # si c'est un surlignage commun
                    liste = [[self.etiquette.speedGS], self.etiquette.ligneDeux,
                             self.etiquette.ligneTrois, self.etiquette.ligneQuatre, self.etiquette.ligneCinq]
                    indexLigne = 0
                    index = 0
                    # on trouve l'index du bouton
                    for indexLigne in range(5):
                        ligne = liste[indexLigne]
                        if event.ui_element in ligne:
                            index = ligne.index(event.ui_element)
                            break
                    return self.Id, 'HighlightBouton', (indexLigne, index)

                elif event.ui_element in self.etiquette.surlignageLoc:
                    # si c'est un surlignage local (que sur mon écran)
                    toggle_surlignage(event.ui_element)

        if event.ui_element == self.bouton:

            if conflitBool:
                self.conflitSelected = not self.conflitSelected
                return None

            if event.mouse_button == 2 and not pilote:  # clic milieu
                return self.Id, 'Warning'

            elif event.mouse_button == 3:
                if pilote:  # si on est en pilote alors ça supp l'avion
                    return self.Id, 'Remove'
                self.locWarning = not self.locWarning  # toggle les warnings locs

        elif event.ui_element == self.etiquette.indicatif:

            if event.mouse_button == 3 and pilote:
                return self.Id, 'EtatFreq', None

            elif event.mouse_button == 1 and not pilote:
                return 'menuATC'

            elif event.mouse_button == 3 and self.papa.integreOrganique and (
                    self.etiquette.indicatif.get_object_ids()[1] in ['@etiquetteBold', '@etiquetteBoldBlue']):

                self.unBold()

        elif event.ui_element == self.etiquette.speedGS and not self.papa.integreOrganique and not pilote:
            self.unBold()
            return self.Id, 'Integre'

        elif event.ui_element == self.etiquette.XPT and event.mouse_button == 3 and not pilote:
            self.drawRouteBool = not self.drawRouteBool

        elif event.ui_element == self.etiquette.XPT and event.mouse_button == 1:
            return 'XPT'

        elif event.ui_element == self.etiquette.DCT and event.mouse_button == 1:
            return 'DCT'

        elif event.ui_element == self.etiquette.DCT and event.mouse_button == 2:
            return 'C_HDG'

        elif event.ui_element == self.etiquette.XFL and event.mouse_button == 1:
            return 'XFL'

        elif event.ui_element == self.etiquette.PFL and event.mouse_button == 1:
            return 'PFL'

        elif event.ui_element == self.etiquette.CFL and event.mouse_button == 1:
            return 'CFL'

        elif event.ui_element == self.etiquette.AFL and event.mouse_button == 1 and pilote:
            return 'FL'

        elif (event.ui_element == self.etiquette.clearedSpeed and event.mouse_button == 1 and
              (self.papa.machMode or self.papa.clearedMach) and not self.papa.clearedIAS):

            return 'C_Mach'

        elif event.ui_element == self.etiquette.clearedSpeed and event.mouse_button == 1:
            return 'C_IAS'

        elif event.ui_element == self.etiquette.rate and event.mouse_button == 1:
            return 'C_Rate'

    def checkEtiquetteOnHover(self):
        """
        Vérifie si on doit ou non étendre l'étiquette
        :return: True si l'event appartient à cette étiquette
        """

        if self.etiquette.container.are_contents_hovered():
            self.etiquetteExtended = True
            return True
        return False

    def checkStillHovered(self):

        """
        Vérifie si on doit ou non désétendre l'étiquette
        """

        mouse = pygame.mouse.get_pos()
        rect = self.etiquette.container.get_abs_rect()

        if not (rect[0] <= mouse[0] <= rect[0] + rect[2] and rect[1] <= mouse[1] <= rect[1] + rect[3]):
            self.etiquetteExtended = False
            self.etiquette.downlink = False

    def extendEtiquette(self, force=False):
        """
        Étend ou range l'étiquette
        :param force: si on veut forcer le rangement de l'etiquette. Utile quand on doit cacher certains boutons
         après un changement (de surlignage par exemple)
        """

        if self.etiquetteExtended and not self.etiquette.extended:  # si on doit etendre et elle n'est pas étendue
            self.etiquette.extended = True

            for ligne in [self.etiquette.ligneDeux, self.etiquette.ligneTrois, self.etiquette.ligneQuatre]:
                for bouton in ligne:
                    bouton.show()

        elif (self.etiquette.extended and not self.etiquetteExtended) or force:
            # si on doit rentrer et elle est étendue
            self.etiquette.extended = False

            if self.etiquette.type_dest.get_object_ids()[1][-4:] != 'Blue':
                self.etiquette.type_dest.hide()

            if self.etiquette.DCT.get_object_ids()[1][-4:] != 'Blue' and not self.papa.clearedHeading:
                self.etiquette.DCT.hide()
            else:
                self.etiquette.DCT.show()

            if self.etiquette.clearedSpeed.get_object_ids()[1][-4:] != 'Blue' and not self.papa.clearedIAS and not self.papa.clearedMach:
                self.etiquette.clearedSpeed.hide()
            else:
                self.etiquette.clearedSpeed.show()

            if self.etiquette.rate.get_object_ids()[1][-4:] != 'Blue' and not self.papa.clearedRate:
                self.etiquette.rate.hide()
            else:
                self.etiquette.rate.show()

            if self.etiquette.nextSector.get_object_ids()[1][-4:] != 'Blue':
                self.etiquette.nextSector.hide()

            if self.papa.XFL == self.papa.CFL and self.etiquette.XFL.get_object_ids()[1][-4:] != 'Blue':
                self.etiquette.XFL.hide()

            if self.papa.CFL == round(self.papa.altitude / 100) and self.etiquette.CFL.get_object_ids()[1][-4:] != 'Blue':
                self.etiquette.CFL.hide()

            if self.etiquette.PFL.get_object_ids()[1][-4:] != 'Blue':
                self.etiquette.PFL.hide()

        if self.etiquette.downlink:

            self.etiquette.selectedAlti.show()
            self.etiquette.selectedHeading.show()
            self.etiquette.selectedSpeed.show()

        else:

            if self.etiquette.selectedAlti.get_object_ids()[1][-4:] != 'Blue':
                self.etiquette.selectedAlti.hide()

            if self.etiquette.selectedSpeed.get_object_ids()[1][-4:] != 'Blue':
                self.etiquette.selectedSpeed.hide()

            if self.etiquette.selectedHeading.get_object_ids()[1][-4:] != 'Blue':
                self.etiquette.selectedHeading.hide()

    def checkHighlight(self, papa):

        liste = [[self.etiquette.speedGS], self.etiquette.ligneDeux,
                 self.etiquette.ligneTrois, self.etiquette.ligneQuatre, self.etiquette.ligneCinq]

        # dans cette boucle, on surligne les nouveaux et on prépare la boucle suivante
        for boutonTuple in papa.boutonsHighlight:

            # on enlève les boutons qu'on surligne pour pouvoir ensuite
            # enlever le surlignage sur les boutons qui ne sont plus à surligner (prep de la prochaine boucle)
            if boutonTuple in self.papa.boutonsHighlight:
                self.papa.boutonsHighlight.remove(boutonTuple)

            bouton = liste[boutonTuple[0]][boutonTuple[1]]
            typeTheme = bouton.get_object_ids()[1]  # relate de la couleur du bg et du gras ou non
            couleur = bouton.get_class_ids()[1]  # couleur du texte

            if typeTheme in ['@etiquetteBold', '@etiquetteBoldBlue']:  # on check le gras pour le garder ensuite
                bouton.change_object_id(pygame_gui.core.ObjectID('@etiquetteBoldBlue', couleur))
            else:
                bouton.change_object_id(pygame_gui.core.ObjectID('@etiquetteBlue', couleur))

            # on montre le bouton, il faut donc calculer sa distance à gauche
            distance = interface.updateDistanceGauche(liste[boutonTuple[0]][:boutonTuple[1]])
            bouton.set_relative_position((distance, 0))
            bouton.show()

        # dans cette boucle, on enlève le surlignage
        for boutonTuple in self.papa.boutonsHighlight:

            bouton = liste[boutonTuple[0]][boutonTuple[1]]
            typeTheme = bouton.get_object_ids()[1]  # relate de la couleur du bg et du gras ou non
            couleur = bouton.get_class_ids()[1]  # couleur du texte

            if typeTheme in ['@etiquetteBold', '@etiquetteBoldBlue']:  # on check le gras pour le garder ensuite
                bouton.change_object_id(pygame_gui.core.ObjectID('@etiquetteBold', couleur))
            else:
                bouton.change_object_id(pygame_gui.core.ObjectID('@etiquette', couleur))

            self.extendEtiquette(force=True)

    def unBold(self) -> None:
        """
        Dégraisse l'étiquette de l'avion
        """
        for ligne in [[self.etiquette.speedGS], self.etiquette.ligneDeux,
                      self.etiquette.ligneTrois, self.etiquette.ligneQuatre]:

            for bouton in ligne:
                couleur = bouton.get_class_ids()[1]  # on récupère la couleur du bouton
                if bouton.get_object_ids()[1] in ['@etiquetteBoldBlue', '@etiquetteBlue']:
                    nouvelObjID = '@etiquetteBlue'
                else:
                    nouvelObjID = '@etiquette'
                bouton.change_object_id(pygame_gui.core.ObjectID(nouvelObjID, couleur))

    def regraissage_methodique(self, papa):
        """
        Véridie si des valeurs boutons ont changé et les regraisse si tel est le cas
        :return:
        """

        if self.papa.XPT != papa.XPT:
            print(self.boldXPT)
            if self.boldXPT:
                bold(self.etiquette.XPT)
                bold(self.etiquette.indicatif)
            else:
                self.boldXPT = True

        if self.papa.XFL != papa.XFL:
            if self.boldXFL:
                bold(self.etiquette.XFL)
                bold(self.etiquette.indicatif)
            else:
                self.boldXFL = True

    def updateEtatFrequence(self, etat) -> None:

        """
        Met à jour la couleur des boutons en fonction de l'état fréquence.
        :param etat:
        :return:
        """

        if etat == 'previousShoot':
            gras = self.etiquette.indicatif.get_object_ids()[1]  # on regarde si le bouton est en gras ou non
            self.etiquette.indicatif.change_object_id(pygame_gui.core.ObjectID(gras, 'blanc'))

        elif etat == 'inFreq':

            for ligne in [[self.etiquette.speedGS], self.etiquette.ligneDeux,
                          self.etiquette.ligneTrois, self.etiquette.ligneQuatre]:

                for bouton in ligne:
                    gras = bouton.get_object_ids()[1]  # on regarde si le bouton est en gras ou non
                    bouton.change_object_id(pygame_gui.core.ObjectID(gras, 'blanc'))

        elif etat == 'nextCoord':

            gras = self.etiquette.XPT.get_object_ids()[1]  # on regarde si le bouton est en gras ou non
            self.etiquette.XPT.change_object_id(pygame_gui.core.ObjectID(gras, 'marron'))

            gras = self.etiquette.nextSector.get_object_ids()[1]  # on regarde si le bouton est en gras ou non
            self.etiquette.nextSector.change_object_id(pygame_gui.core.ObjectID(gras, 'marron'))

        elif etat == 'nextShoot':
            gras = self.etiquette.indicatif.get_object_ids()[1]  # on regarde si le bouton est en gras ou non
            self.etiquette.indicatif.change_object_id(pygame_gui.core.ObjectID(gras, 'marron'))

        elif etat == 'nextFreq':

            for ligne in [[self.etiquette.speedGS], self.etiquette.ligneDeux,
                          self.etiquette.ligneTrois, self.etiquette.ligneQuatre]:

                for bouton in ligne:
                    gras = bouton.get_object_ids()[1]  # on regarde si le bouton est en gras ou non
                    bouton.change_object_id(pygame_gui.core.ObjectID(gras, 'marron'))

        self.update_theme_downlink()

    def update_theme_downlink(self):
        """
        Mets à jour l'apparence des boutons downlink
        :return:
        """
        couleur = self.etiquette.speedGS.get_class_ids()[1]
        print(couleur)
        objet = pygame_gui.core.ObjectID(self.etiquette.selectedAlti.get_object_ids()[1], couleur)
        self.etiquette.selectedAlti.change_object_id(objet)

        objet = pygame_gui.core.ObjectID(self.etiquette.selectedHeading.get_object_ids()[1], couleur)
        self.etiquette.selectedHeading.change_object_id(objet)

        objet = pygame_gui.core.ObjectID(self.etiquette.selectedSpeed.get_object_ids()[1], couleur)
        self.etiquette.selectedSpeed.change_object_id(objet)

    def kill(self):
        self.bouton.kill()
        self.etiquette.kill()

    def update(self, papa):

        # on vérifie que l'état freq est bien celui d'après
        if liste_etat_freq.index(self.papa.etatFrequence) < liste_etat_freq.index(papa.etatFrequence):
            self.updateEtatFrequence(papa.etatFrequence)

        elif liste_etat_freq.index(self.papa.etatFrequence) > liste_etat_freq.index(papa.etatFrequence):
            self.papa.etatFrequence = papa.etatFrequence
            etatFrequenceInit(self)  # si c'est un état freq précédent alors, on repart depuis le début

        # on vérifie que le surlignage des boutons est le même que sur le dernier paquet
        if self.papa.boutonsHighlight != papa.boutonsHighlight:
            self.checkHighlight(papa)  # s'il a changé, on met à jour le surlignage des boutons

        if (self.papa.clearedRate != papa.clearedRate or self.papa.clearedIAS != papa.clearedIAS
                or self.papa.clearedMach != papa.clearedMach or self.papa.clearedHeading != papa.clearedHeading):
            # ici, on étend l'étiquette si certains paramètres qui forcent l'apparition de boutons ont changé
            self.papa = papa
            self.extendEtiquette(True)

        self.regraissage_methodique(papa)

        self.papa = papa

    def etiquetteDrag(self) -> None:

        mouse = pygame.mouse.get_pos()

        self.etiquetteOffsetX = mouse[0] - self.dragOffset[0] - self.affX
        self.etiquetteOffsetY = mouse[1] - self.dragOffset[1] - self.affY


def bold(bouton) -> None:
    """
    Graisse un bouton de l'étiquette
    """

    couleur = bouton.get_class_ids()[1]  # on récupère la couleur du bouton
    if bouton.get_object_ids()[1] == '@etiquetteBlue':
        nouvelObjID = '@etiquetteBoldBlue'
    else:
        nouvelObjID = '@etiquetteBold'
    bouton.change_object_id(pygame_gui.core.ObjectID(nouvelObjID, couleur))


def toggle_surlignage(bouton) -> None:
    """
    Toggle le surlignage d'un bouton de l'étiquette
    """

    couleur = bouton.get_class_ids()[1]  # on récupère la couleur du bouton
    objet = bouton.get_object_ids()[1]
    if objet[-4:] == 'Blue':
        if objet == '@etiquetteBold':
            nouvelObjID = '@etiquetteBold'
        else:
            nouvelObjID = '@etiquette'
    else:
        if objet == '@etiquetteBold':
            nouvelObjID = '@etiquetteBoldBlue'
        else:
            nouvelObjID = '@etiquetteBlue'

    bouton.change_object_id(pygame_gui.core.ObjectID(nouvelObjID, couleur))


def calculateEtiquetteOffset(container) -> tuple[float, float]:
    """
    Calcule l'offset d'un container par rapport à la position de la souris
    :param container: Le container de l'étiquette avec lequel on veut l'offset
    :return:
    """

    posEtiquette = container.get_abs_rect()
    mouse = pygame.mouse.get_pos()
    dragOffset = (mouse[0] - posEtiquette[0], mouse[1] - posEtiquette[1])

    return dragOffset
