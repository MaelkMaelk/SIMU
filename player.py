from typing import Iterable

import pygame
import math
import pygame_gui

plotSize = 8
timeConstant = 8 / 3600


def calculateHeading(x, y, xPoint, yPoint):
    if y > yPoint:
        if x > xPoint:
            heading = (math.atan(abs(y - yPoint) / (abs(x - xPoint)))) * 180 / math.pi
            heading += 270
        else:
            heading = (math.atan(abs(x - xPoint) / (abs(y - yPoint)))) * 180 / math.pi
    elif x > xPoint:
        heading = (math.atan(abs(x - xPoint) / (abs(y - yPoint)))) * 180 / math.pi
        heading += 180
    else:
        heading = (math.atan(abs(y - yPoint) / (abs(x - xPoint)))) * 180 / math.pi
        heading += 90

    heading = heading % 360
    return heading


class Game:
    def __init__(self):
        self.ready = False
        self.paused = True


class Packet:

    def __init__(self, Id, game=None, dictAvions=None, requests=None, map=None, perfos=None):
        self.Id = Id
        self.game = game
        self.dictAvions = dictAvions
        self.requests = requests
        self.map = map
        self.perfos = perfos


class AvionPacket:
    global timeConstant
    global plotSize

    def __init__(self, mapScale, Id, indicatif, aircraft, perfos, x, y, altitude, route, heading=None, PFL=None):
        self.Id = Id
        self.indicatif = indicatif
        self.aircraft = aircraft
        self.x = x
        self.y = y
        self.comete = []
        self.heading = heading
        self.speedDis = perfos[0]
        self.speed = perfos[0] / mapScale * timeConstant
        self.altitude = altitude
        self.warning = False
        self.part = False
        self.altitudeEvoTxt = '-'
        self.perfos = perfos
        self.coordination = 0

        # perfo
        self.turnRate = 12
        self.ROC = perfos[-1] / 6000 * 8
        self.ROD = perfos[-2] / 6000 * 8

        # ROUTE
        self.routeFull = list(route)
        self.route = dict(route[2])
        self.last = route[1]
        self.PFL = PFL
        for sortie in self.routeFull[3]:
            if sortie[1] < self.PFL < sortie[2]:
                self.sortie = sortie[0]
        self.headingMode = False
        self.nextPointValue = 0
        if list(self.route.values())[0][1] < list(self.route.values())[1][
            1]:  # on trouve l'endroit ou se situe l'avion pour savoir quel est son premier point
            for point in list(self.route.values()):
                if point[1] > self.y:
                    break
                self.nextPointValue += 1
        else:
            for point in list(self.route.values()):
                if point[1] < self.y:
                    break
                self.nextPointValue += 1
        if self.nextPointValue < len(self.route):
            self.nextPoint = list(self.route.keys())[self.nextPointValue]
        self.pointHeading = 0

        # heading
        if heading is not None:
            self.heading = heading
        else:
            self.heading = calculateHeading(self.x, self.y, self.route[self.nextPoint][0],
                                            self.route[self.nextPoint][1])
        self.headingRad = (self.heading - 90) / 180 * math.pi

        # TARGETS and spd for altitude/heading etc...
        self.targetFL = self.altitude
        self.targetHead = self.heading

    def Cwarning(self):
        self.warning = not self.warning

    def Cpart(self):
        self.part = not self.part

    def Cmouvement(self):
        if self.coordination == 0:
            self.coordination = 1
        else:
            self.coordination = 2

    def CnextPoint(self, nextPoint):
        self.nextPoint = nextPoint
        for i in range(len(self.route.keys())):
            if list(self.route.keys())[i] == nextPoint:
                break
        self.nextPointValue = i

    def move(self):
        # heading update
        if self.headingMode:
            if self.heading != self.targetHead:
                if abs(self.heading - self.targetHead) <= self.turnRate:
                    self.heading = self.targetHead
                elif abs(self.heading - self.targetHead) > 180:
                    self.heading = (self.heading + self.turnRate * (self.heading - self.targetHead) / abs(
                        self.heading - self.targetHead)) % 360
                else:
                    self.heading -= self.turnRate * (self.heading - self.targetHead) / abs(
                        self.heading - self.targetHead)

        else:
            if math.sqrt((self.x - self.route[self.nextPoint][0]) ** 2 + (
                    self.y - self.route[self.nextPoint][1]) ** 2) <= 2 * self.speed:

                if self.nextPointValue + 1 == len(self.route):
                    self.headingMode = True
                else:
                    self.nextPointValue += 1
                    self.nextPoint = list(self.route.keys())[self.nextPointValue]
            self.pointHeading = calculateHeading(self.x, self.y, self.route[self.nextPoint][0],
                                                 self.route[self.nextPoint][1])

            if self.heading != self.pointHeading:
                if abs(self.heading - self.pointHeading) <= self.turnRate:
                    self.heading = self.pointHeading
                elif abs(self.heading - self.pointHeading) > 180:
                    self.heading = (self.heading + self.turnRate * (self.heading - self.pointHeading) / abs(
                        self.heading - self.pointHeading)) % 360
                else:
                    self.heading -= self.turnRate * (self.heading - self.pointHeading) / abs(
                        self.heading - self.pointHeading)

        # altitude update
        if self.altitude != self.targetFL:
            if self.altitude - self.targetFL > 0:
                if abs(self.altitude - self.targetFL) <= self.ROD:
                    self.altitude = self.targetFL
                    self.altitudeEvoTxt = '-'
                else:
                    self.altitude -= self.ROD
                    self.altitudeEvoTxt = '↘'
            else:
                if abs(self.altitude - self.targetFL) <= self.ROC:
                    self.altitude = self.targetFL
                    self.altitudeEvoTxt = '-'
                else:
                    self.altitude += self.ROC
                    self.altitudeEvoTxt = '↗'

        self.headingRad = (self.heading - 90) / 180 * math.pi

        # comete
        if len(self.comete) >= 6:
            self.comete = self.comete[1:6]
        self.comete.append((self.x + plotSize, self.y + plotSize))

        # movement
        self.x += self.speed * math.cos(self.headingRad)
        self.y += self.speed * math.sin(self.headingRad)

class Avion:
    global timeConstant
    global plotSize

    def __init__(self, Id, Papa, mapScale):
        self.Papa = Papa
        self.Id = Id
        self.indicatif = Papa.indicatif
        self.aircraft = Papa.aircraft
        self.x = Papa.x
        self.y = Papa.y
        self.comete = Papa.comete
        self.speedDis = str(Papa.speedDis)[0:2]
        self.PFL = Papa.PFL
        self.speed = Papa.speed
        self.altitude = Papa.altitude
        self.altitudeEvoTxt = '-'
        self.bouton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.x, self.y), (20, 20)), text='')
        self.bouton.generate_click_events_from: Iterable[int] = frozenset(
            [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])

        self.heading = Papa.heading
        self.headingRad = Papa.headingRad

        # sortie
        self.last = Papa.last
        self.sortie = Papa.sortie

        # size
        self.eHeight = 68
        self.eWidth = 60
        self.size = plotSize

        # Radar display
        self.warning = Papa.warning
        self.part = Papa.part
        self.coordination = 0  # 0 = noir, 1 = blanc, 2 = bleu
        self.onFrequency = False
        self.PFLaff = False

        # etiquette
        self.etiquetteX = self.x + 60
        self.etiquetteY = self.y - 60
        self.etiquetteRect = pygame.Rect(self.etiquetteX, self.etiquetteY - 60, self.eWidth, self.eHeight)
        self.etiquettePos = 0

        # drawRoute
        self.drawRoute = False

        # Zoom & scroll

        self.affX = 0
        self.affY = 0

    def draw(self, win, zoom, scroll, vecteurs, vecteurSetting, typeAff):
        # updates
        self.affX = self.x * zoom + scroll[0]
        self.affY = self.y * zoom + scroll[1]

        if typeAff:
            self.typeBouton.show()
        else:
            self.typeBouton.hide()

        value = 60
        if self.etiquettePos % 4 == 0:
            self.etiquetteX = self.affX + self.size + value
            self.etiquetteY = self.affY + self.size - value
            self.etiquetteCont.relative_rect = pygame.Rect(
                (self.etiquetteX, self.etiquetteY - self.etiquetteCont.rect[3]), (-1, -1))
        elif self.etiquettePos % 4 == 1:
            self.etiquetteX = self.affX + self.size + value
            self.etiquetteY = self.affY + self.size + value
            self.etiquetteCont.relative_rect = pygame.Rect((self.etiquetteX, self.etiquetteY), (-1, -1))
        elif self.etiquettePos % 4 == 2:
            self.etiquetteX = self.affX + self.size - value
            self.etiquetteY = self.affY + self.size + value
            self.etiquetteCont.relative_rect = pygame.Rect(
                (self.etiquetteX - self.etiquetteCont.rect[2], self.etiquetteY), (-1, -1))
        else:
            self.etiquetteX = self.affX + self.size - value
            self.etiquetteY = self.affY + self.size - value
            self.etiquetteCont.relative_rect = pygame.Rect(
                (self.etiquetteX - self.etiquetteCont.rect[2], self.etiquetteY - self.etiquetteCont.rect[3]), (-1, -1))
        self.altitudeBouton.text = str(round(self.altitude))
        self.altitudeBouton.rebuild()
        self.etiquetteCont.rebuild()
        self.etiquetteCont.update_containing_rect_position()

        # altitude evo
        self.altitudeEvoTxtDis.text = self.altitudeEvoTxt
        self.altitudeEvoTxtDis.rebuild()

        # Vrai dessin

        if self.warning:
            color = (255, 120, 60)
            pygame.draw.line(win, color, (self.affX + self.size, self.affY + self.size), (
                self.affX + self.size + self.speed * 60 / 8 * vecteurSetting * zoom * math.cos(self.headingRad),
                self.affY + self.size + self.speed * 60 / 8 * vecteurSetting * zoom * math.sin(self.headingRad)), 2)
            pygame.draw.rect(win, color, (self.affX, self.affY, self.size * 2, self.size * 2), 1)
            for i in range(1, vecteurSetting + 1):
                pygame.draw.circle(win, color, (self.affX + self.size +
                                                self.speed * 60 / 8 * i * zoom * math.cos(self.headingRad),
                                                self.affY + self.size +
                                                self.speed * 60 / 8 * i * zoom * math.sin(self.headingRad)), 2)
        elif vecteurs:
            color = (255, 255, 255)
            pygame.draw.rect(win, color, (self.affX, self.affY, self.size * 2, self.size * 2), 1)
            pygame.draw.line(win, color, (self.affX + self.size, self.affY + self.size), (
                self.affX + self.size + self.speed * 60 / 8 * vecteurSetting * zoom * math.cos(self.headingRad),
                self.affY + self.size + self.speed * 60 / 8 * vecteurSetting * zoom * math.sin(self.headingRad)), 1)
            for i in range(1, vecteurSetting + 1):
                pygame.draw.circle(win, color, (self.affX + self.size +
                                                self.speed * 60 / 8 * i * zoom * math.cos(self.headingRad),
                                                self.affY + self.size +
                                                self.speed * 60 / 8 * i * zoom * math.sin(self.headingRad)), 2)
        else:
            color = (255, 255, 255)
            pygame.draw.rect(win, color, (self.affX, self.affY, self.size * 2, self.size * 2), 1)
        radius = 1
        for plot in self.comete:
            affPlot = [(plot[0] - self.size) * zoom + self.size + scroll[0],
                       (plot[1] - self.size) * zoom + self.size + scroll[1]]
            pygame.draw.circle(win, color, affPlot, radius, 1)
            radius += 1
        pygame.draw.line(win, color, (self.affX + self.size, self.affY + self.size), (self.etiquetteX, self.etiquetteY))

        # PART
        if self.part:
            self.indicatifBouton.select()
        else:
            self.indicatifBouton.unselect()

        # Coord
        if self.coordination == 2:
            self.sortieBouton.disable()
        elif self.coordination == 1:
            self.sortieBouton.select()

    def drawPilote(self, win, zoom, scroll, vecteurs, vecteurSetting, typeAff):
        # updates
        self.affX = self.x * zoom + scroll[0]
        self.affY = self.y * zoom + scroll[1]

        value = 60
        if self.etiquettePos % 4 == 0:
            self.etiquetteX = self.affX + self.size + value
            self.etiquetteY = self.affY + self.size - value
            self.etiquetteCont.relative_rect = pygame.Rect(
                (self.etiquetteX, self.etiquetteY - self.etiquetteCont.rect[3]), (-1, -1))
        elif self.etiquettePos % 4 == 1:
            self.etiquetteX = self.affX + self.size + value
            self.etiquetteY = self.affY + self.size + value
            self.etiquetteCont.relative_rect = pygame.Rect((self.etiquetteX, self.etiquetteY), (-1, -1))
        elif self.etiquettePos % 4 == 2:
            self.etiquetteX = self.affX + self.size - value
            self.etiquetteY = self.affY + self.size + value
            self.etiquetteCont.relative_rect = pygame.Rect(
                (self.etiquetteX - self.etiquetteCont.rect[2], self.etiquetteY), (-1, -1))
        else:
            self.etiquetteX = self.affX + self.size - value
            self.etiquetteY = self.affY + self.size - value
            self.etiquetteCont.relative_rect = pygame.Rect(
                (self.etiquetteX - self.etiquetteCont.rect[2], self.etiquetteY - self.etiquetteCont.rect[3]), (-1, -1))
        self.altitudeBouton.text = str(round(self.altitude))
        self.altitudeBouton.rebuild()
        self.etiquetteCont.rebuild()
        self.etiquetteCont.update_containing_rect_position()

        # altitude evo
        self.altitudeEvoTxtDis.text = self.altitudeEvoTxt
        self.altitudeEvoTxtDis.rebuild()

        # Vrai dessin
        if self.onFrequency:
            color = (0, 255, 0)
        else:
            color = (204, 85, 0)

        if typeAff:
            self.typeBouton.show()
        else:
            self.typeBouton.hide()
        if vecteurs:
            pygame.draw.rect(win, color, (self.affX, self.affY, self.size * 2, self.size * 2), 1)
            pygame.draw.line(win, color, (self.affX + self.size, self.affY + self.size), (
                self.affX + self.size + self.speed * 60 / 8 * vecteurSetting * zoom * math.cos(self.headingRad),
                self.affY + self.size + self.speed * 60 / 8 * vecteurSetting * zoom * math.sin(self.headingRad)), 1)
            for i in range(1, vecteurSetting + 1):
                pygame.draw.circle(win, color, (self.affX + self.size +
                                                self.speed * 60 / 8 * i * zoom * math.cos(self.headingRad),
                                                self.affY + self.size +
                                                self.speed * 60 / 8 * i * zoom * math.sin(self.headingRad)), 2)
        else:
            pygame.draw.rect(win, color, (self.affX, self.affY, self.size * 2, self.size * 2), 1)
        radius = 1
        for plot in self.comete:
            affPlot = [(plot[0] - self.size) * zoom + self.size + scroll[0],
                       (plot[1] - self.size) * zoom + self.size + scroll[1]]
            pygame.draw.circle(win, color, affPlot, radius, 1)
            radius += 1
        pygame.draw.line(win, color, (self.affX + self.size, self.affY + self.size), (self.etiquetteX, self.etiquetteY))

        # PART
        self.indicatifBouton.unselect()

        # Coord
        if self.coordination ==2:
            self.sortieBouton.disable()
        elif self.coordination == 1:
            self.sortieBouton.select()




    def update(self, Papa, zoom, scroll, mapScale):
        self.heading = Papa.heading
        self.headingRad = Papa.headingRad
        self.indicatif = Papa.indicatif
        self.x = Papa.x
        self.y = Papa.y
        self.comete = Papa.comete
        self.speed = Papa.speed

        self.altitude = Papa.altitude
        self.altitudeEvoTxt = Papa.altitudeEvoTxt

        # Radar display
        self.warning = Papa.warning
        self.part = Papa.part
        self.coordination = Papa.coordination

        # zoom & scroll

        self.affX = self.x * zoom + scroll[0]
        self.affY = self.y * zoom + scroll[1]

        # ROUTE

        self.route = Papa.route
        self.PFL = Papa.PFL

        # bouton
        self.bouton.rect = pygame.Rect((self.affX, self.affY), (20, 20))
        self.bouton.rebuild()
        self.PFLbouton.text = str(Papa.PFL)
        self.PFLbouton.rebuild()
        self.altitudeEvoTxtDis.text = Papa.altitudeEvoTxt

        self.bouton.rect = pygame.Rect((self.affX, self.affY), (20, 20))
        self.bouton.rebuild()

        self.altitudeBouton.text = str(self.altitude)
        self.altitudeBouton.rebuild()

        # etiquette

    def etiquetteGen(self, manager):
        self.etiquetteCont = pygame_gui.core.ui_container.UIContainer(pygame.Rect((0, 0), (94, 68)), manager=manager)
        self.speedBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, 17)), text=str(self.speedDis),
            container=self.etiquetteCont, object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))

        self.typeBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((5, 0), (-1, 17)), text=self.aircraft,
            container=self.etiquetteCont, anchors={'left': 'left', 'left_target': self.speedBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))

        self.indicatifBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, 17)), text=str(self.indicatif),
            container=self.etiquetteCont, anchors={'top': 'top', 'top_target': self.speedBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))

        self.altitudeBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (30, 18)), text=str(self.altitude),
            container=self.etiquetteCont, anchors={'top': 'top', 'top_target': self.indicatifBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))

        self.altitudeEvoTxtDis = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((3, 0), (10, 17)), text='-',
                                                             container=self.etiquetteCont,
                                                             anchors={'left': 'left',
                                                                      'left_target': self.altitudeBouton,
                                                                      'top': 'top',
                                                                      'top_target': self.indicatifBouton},
                                                             object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.routeBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, 17)), text=self.last,
            container=self.etiquetteCont, anchors={'top': 'top', 'top_target': self.altitudeBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))

        self.PFLbouton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((1, 0), (28, 17)), text=str(self.PFL),
                                                      container=self.etiquetteCont, anchors={'left': 'left',
                                                                                             'left_target': self.routeBouton,
                                                                                             'top': 'top',
                                                                                             'top_target': self.altitudeBouton},
                                                      object_id= pygame_gui.core.ObjectID('@etiquette', 'autre'))

        self.sortieBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, 17)), text=self.sortie,
            container=self.etiquetteCont, anchors={'left': 'left',
                                                   'left_target': self.PFLbouton, 'top': 'top',
                                                   'top_target': self.altitudeBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'coordBleue'))

        self.indicatifBouton.generate_click_events_from: Iterable[int] = frozenset(
            [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])
        self.etiquetteCont.rebuild()

    def kill(self):
        self.bouton.kill()
        self.etiquetteCont.kill()

class menuDeroulant:

    def __init__(self, x, y, what, value):
        self.Idtuple = (0, 0)
        self.x = x
        self.y = y + 50
        self.what = what
        self.value = value - 100
        self.boutonList = []
        self.cont = None

    def generate(self, Idtuple, x, y, what, value):
        self.Idtuple = Idtuple
        self.x = x
        self.y = y + 50
        self.what = what
        if what == 'Heading':
            self.value = (value + 25) % 360
        else:
            self.value = value + 50
        self.cont = pygame_gui.elements.UIWindow(pygame.Rect((self.x, self.y), (100, 250)))
        self.boutonList.append(pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='+',
            container=self.cont, object_id=pygame_gui.core.ObjectID('caca', '@menu')))
        for i in range(9):
            if what == 'Heading':
                self.value = (self.value - 5) % 360
            else:
                self.value -= 10
            self.boutonList.append(pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (100, 17)), text=str(round(self.value)),
                container=self.cont, anchors={'top': 'top', 'top_target': self.boutonList[i]}))
        self.boutonList.append(pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='-',
            container=self.cont, anchors={'top': 'top', 'top_target': self.boutonList[-1]}))
        self.boutonList[5].select()

    def kill(self):
        if self.cont is not None:
            self.cont.kill()
            self.boutonList = []
            self.cont = 0
        return self.Idtuple

    def increase(self):
        for bouton in self.boutonList[1:-1]:
            if self.what == 'Heading':
                bouton.text = str((int(bouton.text) + 10) % 360)
            else:
                bouton.text = str(int(bouton.text) + 10)
            bouton.rebuild()

    def decrease(self):
        for bouton in self.boutonList[1:-1]:
            if self.what == 'Heading':
                bouton.text = str((int(bouton.text) - 10) % 360)
            else:
                bouton.text = str(int(bouton.text) - 10)
            bouton.rebuild()


class MenuRoute:

    def __init__(self, Idtuple, x, y, route):
        self.Idtuple = Idtuple
        self.window = pygame_gui.elements.UIWindow(pygame.Rect((x, y), (100, 250)))
        self.boutonList = []
        self.route = route
        self.boutonList.append(pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text=list(self.route.keys())[0],
            container=self.window))

        for i in range(1, len(route)):
            self.boutonList.append(pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (100, 17)), text=list(self.route.keys())[i],
                container=self.window, anchors={'top': 'top', 'top_target': self.boutonList[i - 1]}))

    def kill(self):
        self.window.kill()
        return self.Idtuple


class NouvelAvionWindow:

    def __init__(self, routes, avions):
        self.routesFull = routes  # on s'en sert que pour avoir les valeurs de spawn/last au moment de l'apparition
        self.routes = [route[2] for route in routes]
        self.avions = avions

        self.window = pygame_gui.elements.UIWindow(pygame.Rect((250, 250), (600, 340)))
        self.scrollRoutes = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (200, 200)),
                                                                     container=self.window)
        self.scrollAvions = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (200, 200)),
                                                                     container=self.window,
                                                                     anchors={'left': 'left',
                                                                              'left_target': self.scrollRoutes})

        self.routesBoutons = []
        self.routesBoutons.append(pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            text=list(self.routes[0].keys())[0] + " -> " + list(self.routes[0].keys())[-1],
            container=self.scrollRoutes))

        for route in self.routes[1:]:
            self.routesBoutons.append(pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (200, 17)),
                text=list(route.keys())[0] + " -> " + list(route.keys())[-1],
                container=self.scrollRoutes, anchors={'top': 'top', 'top_target': self.routesBoutons[-1]}))

        self.avionsBoutons = []
        self.avionsBoutons.append(pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            text=list(avions.keys())[0],
            container=self.scrollAvions))

        for avion in list(avions.keys())[1:]:
            self.avionsBoutons.append(pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (200, 17)),
                text=avion,
                container=self.scrollAvions, anchors={'top': 'top', 'top_target': self.avionsBoutons[-1]}))
        self.conflitsBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 20), (200, 17)),
            text='Générateur de conflits',
            container=self.window, anchors={'top': 'top', 'top_target': self.scrollAvions, 'left': 'left',
                                            'left_target': self.scrollRoutes})
        self.validationBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 5), (200, 17)),
            text='Ok',
            container=self.window, anchors={'top': 'top', 'top_target': self.conflitsBouton, 'left': 'left',
                                            'left_target': self.scrollRoutes})

        self.indicatiflabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 0), (200, 17)),
                                                          container=self.window,
                                                          anchors={'left': 'left', 'left_target': self.scrollAvions},
                                                          text='Indicatif')
        self.indicatifinput = pygame_gui.elements.UITextEntryBox(relative_rect=pygame.Rect((0, 0), (200, 30)),
                                                                 container=self.window,
                                                                 anchors={'left': 'left',
                                                                          'left_target': self.scrollAvions,
                                                                          'top': 'top',
                                                                          'top_target': self.indicatiflabel})
        self.FLlabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 0), (200, 17)),
                                                   container=self.window,
                                                   anchors={'left': 'left', 'left_target': self.scrollAvions,
                                                            'top': 'top',
                                                            'top_target': self.indicatifinput},
                                                   text='FL')
        self.FLinput = pygame_gui.elements.UITextEntryBox(relative_rect=pygame.Rect((0, 0), (200, 30)),
                                                          container=self.window,
                                                          anchors={'left': 'left', 'left_target': self.scrollAvions,
                                                                   'top': 'top',
                                                                   'top_target': self.FLlabel})
        self.PFLlabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 0), (200, 17)),
                                                   container=self.window,
                                                   anchors={'left': 'left', 'left_target': self.scrollAvions,
                                                            'top': 'top',
                                                            'top_target': self.FLinput},
                                                   text='PFL')
        self.PFLinput = pygame_gui.elements.UITextEntryBox(relative_rect=pygame.Rect((0, 0), (200, 30)),
                                                          container=self.window,
                                                          anchors={'left': 'left', 'left_target': self.scrollAvions,
                                                                   'top': 'top',
                                                                   'top_target': self.PFLlabel})

    def kill(self):
        self.window.kill()

class MenuATC:

    def __init__(self, Idtuple, x, y):
        self.Idtuple = Idtuple
        self.window = pygame_gui.elements.UIWindow(pygame.Rect((x, y), (100, 250)))

        self.partBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='PART',
            container=self.window)

        self.movBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='MVT',
            container=self.window, anchors={'top':'top', 'top_target': self.partBouton})


    def kill(self):
        self.window.kill()
        return self.Idtuple