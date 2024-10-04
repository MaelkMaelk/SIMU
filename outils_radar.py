import pygame
import pygame_gui

import geometry
import math
from valeurs_config import *


class aliSep:

    def __init__(self, lettre):
        self.lettre = lettre
        self.avion1 = None
        self.avion2 = None
        self.distance = None
        self.temps = None

    def linkAvion(self, avion, carte) -> bool:

        """
        Associe un avion. Si un avion est déjà associé alors celà déclenche le calcul de la sep
        :param avion: l'avion à associer
        :param carte: les données de la carte
        :return: si les deux avions ont été associés, renvoies True
        """

        if self.avion2:
            return True

        if not self.avion1:
            self.avion1 = avion
            return False

        self.avion2 = avion

        self.avion1.sep = True
        self.avion2.sep = True

        self.calculation(carte)

        return True

    def calculation(self, carte):

        if not self.avion2:
            return None

        self.temps = geometry.distanceMinie(
            (self.avion1.papa.x, self.avion1.papa.y), self.avion1.papa.speedPx / radarRefresh,
            self.avion1.papa.headingRad,
            (self.avion2.papa.x, self.avion2.papa.y), self.avion2.papa.speedPx / radarRefresh,
            self.avion2.papa.headingRad,
        )

        self.distance = math.sqrt(
            ((self.avion1.papa.x + self.avion1.papa.speedPx / radarRefresh * self.temps * math.cos(
                self.avion1.papa.headingRad)) -
             (self.avion2.papa.x + self.avion2.papa.speedPx / radarRefresh * self.temps * math.cos(
                 self.avion2.papa.headingRad))) ** 2 +
            ((self.avion1.papa.y + self.avion1.papa.speedPx / radarRefresh * self.temps * math.sin(
                self.avion1.papa.headingRad)) -
             (self.avion2.papa.y + self.avion2.papa.speedPx / radarRefresh * self.temps * math.sin(
                 self.avion2.papa.headingRad))) ** 2)

        self.avion1.sepSetting.update({self.lettre: [self.temps, self.distance * carte['mapScale']]})
        self.avion2.sepSetting.update({self.lettre: [self.temps, self.distance * carte['mapScale']]})

    def kill(self):

        if not self.avion2 and self.avion1:
            self.avion1 = None
            return None

        if not self.avion1:
            return None

        self.avion1.sepSetting.pop(self.lettre)
        self.avion2.sepSetting.pop(self.lettre)

        if len(self.avion1.sepSetting) == 0:
            self.avion1.sep = False
        if len(self.avion2.sepSetting) == 0:
            self.avion2.sep = False

        self.avion1 = None
        self.avion2 = None


class conflictGenerator:

    def __init__(self, win, avion, carte):

        size = win.get_size()
        width = size[0] / 3
        height = 40

        self.carte = carte

        self.slider = pygame_gui.elements.UIHorizontalScrollBar(
            pygame.Rect((size[0] / 2 - width / 2, 10), (width, height)),
            visible_percentage=0.3,

        )
        self.valider = pygame_gui.elements.UIButton(
            pygame.Rect((size[0] / 2 + width / 2 + 10, 10), (height, height)),
            text='OK'
        )

        self.avion = None
        self.temps = 0
        self.maxTemps = 60 * 60  # temps en sec, donc 40 min au max
        self.avion = avion
        self.x = None
        self.y = None
        self.spawnDelay = None
        self.drawListe = None

    def checkScrollBar(self, carte):

        """Ajuste la valeur de temps en fonction du slider s'il est scrollé"""

        if self.slider.has_moved_recently:
            self.temps = self.slider.start_percentage * self.maxTemps
            if self.x:
                self.increaseTime(self.temps, carte)

    def checkEvent(self, event):

        """
        Vérifies si les boutons sont appuyés et prend les actions nécessaires.
        :param event:
        :return:
        """
        if event.ui_element == self.valider:
            return self.kill()

    def computeSpawn(self, pos: list[float, float] | tuple[float, float], carte):
        """
        Change la position, ou le delay de spawn de l'avion en fonction de la position voulue et des perfos
        :param pos: La position de conflit choisie
        :param carte: La carte du jeu
        :return:
        """

        points = carte['points']
        route = self.avion.route['points']
        distance = self.temps * self.avion.speedPx / radarRefresh  # quelle distance va parcourir l'avion en ce temps
        distance_calcule = 0

        point2 = points[route[0]['name']]

        p = geometry.findClosestSegment(self.avion.route['points'], pos, carte['points'])[0]

        for index in range(len(route[:route.index(p)])):
            point1 = points[route[index]['name']]
            point2 = points[route[index + 1]['name']]
            distance_calcule += geometry.calculateDistance(point1[0], point1[1], point2[0], point2[1])

        offroadDistance = geometry.calculateDistance(pos[0], pos[1], point2[0], point2[1])
        distance_calcule += offroadDistance

        a = list(range(len(route[:route.index(p) + 1])))
        self.drawListe = []

        if distance_calcule <= distance:  # si on doit parcourir plus que ce qu'on a calculé au spawn
            #  alors on delay le spawn, temps ici en sec
            self.spawnDelay = int((distance - distance_calcule) / self.avion.speedPx * radarRefresh)
            self.x = points[route[0]['name']][0]
            self.y = points[route[0]['name']][1]

            for index in a:
                self.drawListe.append(points[route[index]['name']])

        else:  # si on doit parcourir moins, alors on fait apparaître l'avion plus proche du secteur
            self.spawnDelay = None
            distanceAparcourir = distance_calcule - distance
            index = 0
            found = False
            for index in a:
                point1 = points[route[index]['name']]
                point2 = points[route[index + 1]['name']]
                legDistance = geometry.calculateDistance(point1[0], point1[1], point2[0], point2[1])

                if found:
                    self.drawListe.append(point1)

                elif legDistance >= distanceAparcourir:  # si on doit faire apparaître sur cette branche
                    ratio = distanceAparcourir / legDistance
                    self.x = ratio * (point2[0] - point1[0]) + point1[0]
                    self.y = ratio * (point2[1] - point1[1]) + point1[1]
                    self.drawListe.append((self.x, self.y))
                    self.avion.x = self.x
                    self.avion.y = self.y
                    found = True

                else:
                    distanceAparcourir -= legDistance

        self.drawListe.append(pos)

    def draw(self, win, zoom, scroll) -> None:
        if self.x is None:
            return None
        pygame.draw.circle(win, (255, 255, 0), (self.x * zoom + scroll[0], self.y * zoom + scroll[1]), 3)
        for index in range(len(self.drawListe) - 1):
            point1 = self.drawListe[index]
            point2 = self.drawListe[index + 1]
            pygame.draw.line(win, (255, 255, 0),
                             (point1[0] * zoom + scroll[0], point1[1] * zoom + scroll[1]),
                             (point2[0] * zoom + scroll[0], point2[1] * zoom + scroll[1]))

        if self.spawnDelay:
            font = pygame.font.SysFont('arial', 15)
            img = font.render("Délai à l'apparition: " + str(self.spawnDelay) + "s", True, (170, 170, 255))
            win.blit(img, (self.drawListe[0][0] * zoom + scroll[0], self.drawListe[0][1] * zoom + scroll[1]))

    def increaseTime(self, temps, carte):

        """
        Augmente le temps de dessin sans changer le point de spawn
        :param carte: La carte du jeu
        :param temps: Le nouveau temps de dessin
        :return:
        """
        points = carte['points']
        self.temps = temps
        distance = (self.temps - self.spawnDelay) * self.avion.speedPx / radarRefresh  # quelle distance va parcourir l'avion en ce temps

        startPlot = geometry.findClosestSegment(self.avion.route['points'], (self.x, self.y), points)[1]
        liste = self.avion.route['points'][self.avion.route['points'].index(startPlot):]
        self.drawListe = [(self.x, self.y)]

        point1 = (self.x, self.y)
        self.drawListe.append(point1)
        for index in range(len(liste)):
            point2 = points[liste[index]['name']]

            legDistance = geometry.calculateDistance(point1[0], point1[1], point2[0], point2[1])
            if distance - legDistance <= 0:
                ratio = distance / legDistance
                print(ratio)
                x = ratio * (point2[0] - point1[0]) + point1[0]
                y = ratio * (point2[1] - point1[1]) + point1[1]
                self.drawListe.append(point1)
                self.drawListe.append((x, y))
                break

            else:
                distance -= legDistance
                self.drawListe.append(point2)
            point1 = point2

    def kill(self):
        self.valider.kill()
        self.slider.kill()
        self.avion.findNextPoint(self.carte)
        if self.spawnDelay:
            return self.spawnDelay, self.avion
        return self.avion
