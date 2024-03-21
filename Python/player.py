from typing import Iterable
import numpy as np
import pygame
import math
import pygame_gui

plotSize = 6
radarRefresh = 4
timeConstant = radarRefresh / 3600
listeEtrangers = ['G2', 'M2']
etiquetteLines = 4
nmToFeet = 6076
axe = 74
axePoint = 'BST'


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


def calculateDistance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def calculateAngle(principal, secondaire):
    """Calcul des angles entre deux droites orientées.
    l'angle retourné en 1er est celui en aval de la droite principale et en amont de la secondaire
    :arg principal: droite soit 2 points (x1,y1,x2,y2) dans le sens orienté soit un radial
    :arg secondaire: droite soit 2 points (x1,y1,x2,y2) dans le sens orienté soit un radial
    :returns [angle d'interception, l'autre angle]"""

    # on calcule dabord les radials
    if type(principal) in [list, tuple]:
        principal = calculateHeading(principal[0], principal[1], principal[2], principal[3])
    if type(secondaire) in [list, tuple]:
        secondaire = calculateHeading(secondaire[0], secondaire[1], secondaire[2], secondaire[3])

    # on fait ensuite les soustractions pour obtenir les angles
    if principal <= secondaire and secondaire - principal <= 180:
        return [secondaire - principal, 180 - secondaire + principal]
    elif principal <= secondaire:
        return [principal - secondaire + 360, secondaire - 180 - principal]
    elif principal - secondaire <= 180:
        return [principal - secondaire, 180 - principal + secondaire]
    else:
        return [secondaire - principal + 360, principal - 180 - secondaire]


def calculateIntersection(heading, xAvion, yAvion, radial, point, gameMap = None):
    """calcule l'intersection entre un axe et l'heading de l'avion
    :arg point: le point d'ou part le radial soit (x,y) soit un str d'un point défini ex: 'LTP'
    :arg gameMap: ajouter la gameMap pour avoir la liste des points quand on utilise un str en point"""
    if type(point) is str:
        xPoint = gameMap[0][point][0]
        yPoint = gameMap[0][point][1]
    else:
        xPoint = point[0]
        yPoint = point[1]
    radial = (radial - 90) / 180 * math.pi
    heading = (heading - 90) / 180 * math.pi
    left_side = np.array([[math.cos(heading), -math.cos(radial)], [math.sin(heading), -math.sin(radial)]])
    right_side = np.array([xPoint - xAvion,  yPoint - yAvion])
    return abs(np.linalg.solve(left_side, right_side))  # résoltution du système pour trouver x et y


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
    global listeEtrangers

    def __init__(self, mapScale, listePoints, Id, indicatif, aircraft, perfos, x, y, FL, route, heading=None, PFL=None):
        self.Id = Id
        self.indicatif = indicatif
        self.aircraft = aircraft
        self.x = x
        self.y = y
        self.comete = []
        self.altitude = FL * 100
        self.speedIAS = perfos[0]
        self.speedTAS = self.speedIAS + self.altitude / 200
        self.speed = self.speedTAS / mapScale * timeConstant
        self.altitudeEvoTxt = '-'
        self.perfos = perfos

        # RADAR display
        self.warning = False
        self.part = False
        self.coordination = 0
        self.STCA = False
        self.FLInterro = False
        self.montrer = False

        # perfo
        self.turnRate = 10
        self.maxROC = perfos[-1] / 60 * radarRefresh
        self.maxROD = perfos[-2] / 60 * radarRefresh
        self.evolution = 0  # 0 stable

        # ROUTE format route [nomRoute, routeType, listeRoutePoints, next] points : {caractéristiques eg : nom alti IAS}
        self.routeFull = route
        self.route = route[2]
        self.last = list(self.route)[-1]['name']  # ne sert qu'à l'affichage sorti pour le moment
        if PFL is not None:
            self.PFL = PFL
        else:
            self.PFL = FL
        # for sortie in self.routeFull[3]:
        #    if sortie[1] < self.PFL < sortie[2]:
        #        self.sortie = sortie[0]
        self.sortie = 'caca'
        self.headingMode = False
        self.routeType = self.routeFull[1]
        self.intercept = False
        self.axe = None
        self.attente = {}  # format attente : # radial, IAS, temps, turnRadius si non standard
        if calculateDistance(x, y, listePoints[self.route[0]['name']][0], listePoints[self.route[0]['name']][1]) <= 4 * self.speed:
            self.nextPointValue = 1
        else:
            self.nextPointValue = 0
        self.nextPoint = self.route[self.nextPointValue]
        self.nextRouteListe = route[3]
        if route[3] is not []:
            self.nextRoute = route[3][0]

        # heading
        if heading is not None:
            self.heading = heading
        else:  # points format {name: (x, y, balise, procedure)}
            self.heading = calculateHeading(self.x, self.y, listePoints[self.nextPoint['name']][0],
                                            listePoints[self.nextPoint['name']][1])
        self.headingRad = (self.heading - 90) / 180 * math.pi

        # TARGETS and spd for altitude/heading etc...
        self.targetFL = self.altitude
        self.calculateEvoRate(listePoints)
        self.targetHeading = self.heading

        # radardisp type : arrivée départ transit
        if self.routeFull[1] in ('APP', 'STAR', 'HLDG'):
            self.plotType = 'arrivee'
        elif self.routeFull[1] == 'SID':
            self.plotType = 'depart'
        elif self.routeFull[1] == 'transit':
            self.plotType = 'transit'

    def Cwarning(self):
        self.warning = not self.warning

    def Cpart(self):
        self.part = not self.part

    def Cmouvement(self):
        if self.coordination == 1 and self.sortie in listeEtrangers:
            self.coordination = 2  # enabled
        else:
            self.coordination = 1  # disabled

    def CnextPoint(self, nextPoint):
        for i in range(len(self.route)):
            if self.route[i]['name'] == nextPoint:
                break
        self.nextPoint = self.route[i]
        self.nextPointValue = i

    def changeRoute(self, gameMap, nextRoute=None):
        if nextRoute is not None:
            self.nextRoute = nextRoute
        for route in gameMap[3]:
            if route[0] == self.nextRoute:
                self.routeFull = route
                break

        self.routeType = self.routeFull[1]
        self.route = self.routeFull[2]
        self.nextPointValue = 0
        self.nextPoint = self.route[0]
        self.nextRoute = self.routeFull[3][0]

        if self.routeType == 'HLDG':
            self.HLDGradial = self.route[0]['radial']

            try:
                self.HLDGturnTime = self.route[0]['turnTime'] * 60 / radarRefresh
            except:
                self.HLDGturnTime = 60 / radarRefresh
            self.turnRate = 180 / self.HLDGturnTime

            try:
                self.HLDGoutboundTime = self.route[0]['outboundTime'] * 60 / radarRefresh
            except:
                self.HLDGoutboundTime = 60 / radarRefresh

            try:
                if self.route[0]['rightTurn'] in ['FALSE','false','False']:
                    self.HLDGrightTurn = False
                else:
                    self.HLDGrightTurn = True
            except:
                self.HLDGrightTurn = True

            if self.HLDGrightTurn:
                self.HLDGrightTurnMultiplier = 1
            else:
                self.HLDGrightTurnMultiplier = -1

            self.HLDGentryType = None
            self.inHLDG = False
            self.HLDGtime = 0 #compteur pour savoir ou on est dans le HLDG

    def calculateEvoRate(self, listePoints):

        """Calcule le taux de descente ou de montée pour suivre la procédure,
         change le self.evolution et le TargetFL"""

        altiCible = self.altitude
        for point in self.route[self.nextPointValue:]:
            try:
                altiCible = point['Altitude']
                break
            except:
                pass
        if altiCible != self.altitude:
            self.evolution = ((altiCible - self.altitude) /
                              calculateDistance(self.x, self.y, listePoints[point['name']][0],
                                                listePoints[point['name']][1])) * self.speed
            self.targetFL = altiCible
        else:
            self.evolution = 0

    def changeAxe(self, Axe, gameMap):
        for axeElement in gameMap[5]:
            if Axe == axeElement[0]:
                self.axe = axeElement
                break

    def move(self, gameMap):
        # heading update
        if self.headingMode:
            # interception d'un axe
            if self.intercept:

                if (calculateIntersection(self.heading, self.x, self.y, self.axe[2], self.axe[1], gameMap)[0]
                                       / self.speed) <= (calculateAngle(self.axe[2], self.heading)[0]/2/self.turnRate):
                    self.targetHeading = self.axe[2]

                if self.heading == self.axe[2]:
                    self.intercept = False
                    self.headingMode = False
                    self.changeRoute(gameMap, self.axe[3])

        elif self.routeType == 'HLDG':  # format attente : # radial, IAS, outboundTime, turnTime si non-standard
            if self.inHLDG:  # si l'avion est deja dans l'attente:
                if calculateDistance(self.x, self.y, gameMap[0][self.nextPoint['name']][0],
                                       gameMap[0][self.nextPoint['name']][1]) <= self.speed:

                    self.heading = (self.route[0]['radial'] + 360 + self.HLDGrightTurnMultiplier * 5) % 360
                    self.targetHeading = self.route[0]['radial'] + 180
                    self.HLDGtime = 0

                elif self.HLDGtime >= self.HLDGturnTime * 2 + self.HLDGoutboundTime:
                    self.targetHeading = calculateHeading(self.x, self.y, gameMap[0][self.nextPoint['name']][0],
                                                         gameMap[0][self.nextPoint['name']][1])

                elif self.HLDGtime >= self.HLDGturnTime + self.HLDGoutboundTime:
                    self.heading += self.HLDGrightTurnMultiplier
                    self.targetHeading = self.route[0]['radial']

                self.HLDGtime += 1

            else:  # si il n'est pas dans l'attente:

                # on vérifie que l'avion ai bien son cap final sur la balise et qu'il ne connait pas son entrée
                if self.HLDGentryType is None and self.heading == self.targetHeading:
                    if self.route[0]['rightTurn']:
                        if ((self.route[0]['radial'] + 290) % 360 <= self.heading <
                                (self.route[0]['radial'] + 110) % 360):

                            self.inHLDG = True

                        elif ((self.route[0]['radial'] + 110) % 360 <= self.heading <
                              (self.route[0]['radial'] + 180) % 360):

                            self.HLDGentryType = 'offset_entry'

                        else:
                            self.HLDGentryType = 'parallel_entry'
                    else:
                        if (self.route[0]['radial'] <= self.heading <
                                (self.route[0]['radial'] + 70) % 360):

                            self.HLDGentryType = 'offset_entry'

                        elif (self.route[0]['radial'] + 250) % 360 <= self.heading < self.route[0]['radial']:

                            self.HLDGentryType = 'parallel_entry'

                        else:
                            self.inHLDG = True

                    print(self.HLDGentryType)

                elif self.HLDGentryType == 'offset_entry':
                    if ((calculateDistance(self.x, self.y, gameMap[0][self.nextPoint['name']][0], gameMap[0][self.nextPoint['name']][1]) / self.speed)
                            <= calculateAngle(74, self.heading)[0]/2/self.turnRate) and self.HLDGtime == 0:
                        if self.HLDGrightTurn:
                            self.targetHeading = (self.route[0]['radial'] + 150) % 360
                        else:
                            self.targetHeading = (self.route[0]['radial'] + 210) % 360
                        self.HLDGtime = 1

                    elif self.HLDGtime == self.HLDGoutboundTime:
                        self.targetHeading = self.targetHeading = calculateHeading(self.x, self.y,
                                                                                   gameMap[0][self.nextPoint['name']][0],
                                                                                   gameMap[0][self.nextPoint['name']][1])
                        self.heading = (self.heading + 360 + self.HLDGrightTurnMultiplier * 10) % 360
                        self.inHLDG = True
                        self.HLDGtime = self.HLDGturnTime * 2 + self.HLDGoutboundTime # valeur du temps au rapprochement

                    elif 0 < self.HLDGtime:
                        self.HLDGtime += 1

                else:  # forcément entrée parallel
                    if ((calculateDistance(self.x, self.y, gameMap[0][self.nextPoint['name']][0], gameMap[0][self.nextPoint['name']][1]) / self.speed)
                            <= calculateAngle(74, self.heading)[0] / 2 / self.turnRate) and self.HLDGtime == 0:

                        self.targetHeading = (self.route[0]['radial'] + 180) % 360
                        self.HLDGtime = 1

                    elif self.HLDGtime == self.HLDGoutboundTime:
                        self.targetHeading = self.targetHeading = calculateHeading(self.x, self.y,
                                                                                   gameMap[0][self.nextPoint['name']][
                                                                                       0],
                                                                                   gameMap[0][self.nextPoint['name']][
                                                                                       1])
                        self.heading = (self.heading + 360 - self.HLDGrightTurnMultiplier * 10) % 360 # virage dans le sens opposé au virage de l'attente
                        self.inHLDG = True
                        self.HLDGtime = self.HLDGturnTime * 2 + self.HLDGoutboundTime  # valeur du temps au rapprochement

                    elif 0 < self.HLDGtime:
                        self.HLDGtime += 1

        else:
            if math.sqrt((self.x - gameMap[0][self.nextPoint['name']][0]) ** 2 + (
                    self.y - gameMap[0][self.nextPoint['name']][1]) ** 2) <= 2 * self.speed:

                if self.nextPointValue + 1 == len(self.route):
                    if self.nextRoute == 'land':
                        return True
                    else:
                        self.changeRoute(gameMap)
                else:
                    self.nextPointValue += 1
                    self.nextPoint = self.route[self.nextPointValue]
                    if self.altitude == self.targetFL:
                        self.calculateEvoRate(gameMap[0])

            self.targetHeading = calculateHeading(self.x, self.y, gameMap[0][self.nextPoint['name']][0],
                                             gameMap[0][self.nextPoint['name']][1])

        if self.heading != self.targetHeading:
            if abs(self.heading - self.targetHeading) <= self.turnRate:
                self.heading = self.targetHeading
            elif abs(self.heading - self.targetHeading) > 180:
                self.heading = (self.heading + self.turnRate * (self.heading - self.targetHeading) / abs(
                    self.heading - self.targetHeading)) % 360
            else:
                self.heading -= self.turnRate * (self.heading - self.targetHeading) / abs(
                    self.heading - self.targetHeading)

        # altitude update
        if self.altitude != self.targetFL:
            if self.altitude - self.targetFL > 0:
                if abs(self.altitude - self.targetFL) <= abs(self.evolution):
                    self.altitude = self.targetFL
                    if not self.headingMode:
                        self.calculateEvoRate(gameMap[0])
                else:
                    self.altitude += self.evolution
                    self.altitudeEvoTxt = '↘'
            else:
                if abs(self.altitude - self.targetFL) <= abs(self.evolution):
                    self.altitude = self.targetFL
                    if not self.headingMode:
                        self.calculateEvoRate(gameMap[0])
                else:
                    self.altitude += self.evolution
                    self.altitudeEvoTxt = '↗'
        else:
            self.altitudeEvoTxt = '-'

        self.headingRad = (self.heading - 90) / 180 * math.pi

        # comete
        if len(self.comete) >= 6:
            self.comete = self.comete[1:6]
        self.comete.append((self.x + plotSize, self.y + plotSize))

        # movement
        self.x += self.speed * math.cos(self.headingRad)
        self.y += self.speed * math.sin(self.headingRad)

        self.speedTAS = self.speedIAS + self.altitude / 200
        self.speed = self.speedTAS / gameMap[4] * timeConstant


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
        self.PFL = Papa.PFL
        self.speedTAS = Papa.speedTAS
        self.speedIAS = Papa.speedIAS
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
        self.STCA = Papa.STCA
        self.FLInterro = Papa.FLInterro
        self.montrer = Papa.montrer
        self.plotType = Papa.plotType

        # etiquette
        self.etiquetteX = self.x + 60
        self.etiquetteY = self.y - 60
        self.etiquetteRect = pygame.Rect(self.etiquetteX, self.etiquetteY - 60, self.eWidth, self.eHeight)
        self.etiquettePos = 0

        # drawRoute
        self.drawRoute = False
        self.route = Papa.route
        self.nextRouteListe = Papa.nextRouteListe

        # Zoom & scroll

        self.affX = 0
        self.affY = 0

        # TARGETS and spd for altitude/heading etc...
        self.targetFL = Papa.targetFL
        self.targetHeading = Papa.targetHeading

    def draw(self, win, zoom, scroll, vecteurs, vecteurSetting, typeAff):
        # updates
        self.affX = self.x * zoom + scroll[0]
        self.affY = self.y * zoom + scroll[1]

        # on regarde si le bouton est actif pour décaler les suivants sur la ligne

        if self.STCA and not self.STCAlabel.visible:
            self.STCAlabel.show()
            self.typeBouton.set_relative_position(
                (self.typeBouton.get_relative_rect()[0] + self.STCAlabel.get_abs_rect()[2], 0))
            self.montrerBouton.set_relative_position(
                (self.montrerBouton.get_relative_rect()[0] + self.STCAlabel.get_abs_rect()[2], 0))
            self.flightLVLbouton.set_relative_position(
                (self.flightLVLbouton.get_relative_rect()[0] + self.STCAlabel.get_abs_rect()[2], 0))
        elif not self.STCA and self.STCAlabel.visible:
            self.STCAlabel.hide()
            self.typeBouton.set_relative_position(
                (self.typeBouton.get_relative_rect()[0] - self.STCAlabel.get_abs_rect()[2], 0))
            self.montrerBouton.set_relative_position(
                (self.montrerBouton.get_relative_rect()[0] - self.STCAlabel.get_abs_rect()[2], 0))
            self.flightLVLbouton.set_relative_position(
                (self.flightLVLbouton.get_relative_rect()[0] - self.STCAlabel.get_abs_rect()[2], 0))

        if typeAff and not self.typeBouton.visible:
            self.typeBouton.show()
            self.montrerBouton.set_relative_position(
                (self.montrerBouton.get_relative_rect()[0] + self.typeBouton.get_abs_rect()[2], 0))
            self.flightLVLbouton.set_relative_position(
                (self.flightLVLbouton.get_relative_rect()[0] + self.typeBouton.get_abs_rect()[2], 0))
        elif not typeAff and self.typeBouton.visible:
            self.typeBouton.hide()
            self.montrerBouton.set_relative_position(
                (self.montrerBouton.get_relative_rect()[0] - self.typeBouton.get_abs_rect()[2], 0))
            self.flightLVLbouton.set_relative_position(
                (self.flightLVLbouton.get_relative_rect()[0] - self.typeBouton.get_abs_rect()[2], 0))

        if self.montrer and not self.montrerBouton.visible:
            self.montrerBouton.show()
            self.flightLVLbouton.set_relative_position(
                (self.flightLVLbouton.get_relative_rect()[0] + self.montrerBouton.get_abs_rect()[2], 0))
        elif not self.montrer and self.montrerBouton.visible:
            self.montrerBouton.hide()
            self.flightLVLbouton.set_relative_position(
                (self.flightLVLbouton.get_relative_rect()[0] - self.montrerBouton.get_abs_rect()[2], 0))

        if self.FLInterro and not self.flightLVLbouton.visible:
            self.flightLVLbouton.show()
        elif not self.FLInterro and self.flightLVLbouton.visible:
            self.flightLVLbouton.hide()

        # calcul de la largeur de l'etiquette
        largeur = 0
        for ligne in self.etiquetteList:
            largeurLigne = 0
            for element in ligne:
                if element.visible:
                    largeurLigne += element.get_abs_rect().size[0] + 2
            if largeur < largeurLigne:
                largeur = largeurLigne
        self.etiquetteContainer.rect[2] = largeur

        value = 60  # distance de l'etiquette par rapport au plot
        if self.etiquettePos % 4 == 0:
            self.etiquetteX = self.affX + self.size + value
            self.etiquetteY = self.affY + self.size - value
            self.etiquetteContainer.relative_rect = pygame.Rect(
                (self.etiquetteX, self.etiquetteY - self.etiquetteContainer.rect[3]), (-1, -1))
        elif self.etiquettePos % 4 == 1:
            self.etiquetteX = self.affX + self.size + value
            self.etiquetteY = self.affY + self.size + value
            self.etiquetteContainer.relative_rect = pygame.Rect((self.etiquetteX, self.etiquetteY), (-1, -1))
        elif self.etiquettePos % 4 == 2:
            self.etiquetteX = self.affX + self.size - value
            self.etiquetteY = self.affY + self.size + value
            self.etiquetteContainer.relative_rect = pygame.Rect(
                (self.etiquetteX - self.etiquetteContainer.rect[2], self.etiquetteY), (-1, -1))
        else:
            self.etiquetteX = self.affX + self.size - value
            self.etiquetteY = self.affY + self.size - value
            self.etiquetteContainer.relative_rect = pygame.Rect(
                (self.etiquetteX - self.etiquetteContainer.rect[2], self.etiquetteY - self.etiquetteContainer.rect[3]),
                (-1, -1))
        self.altitudeBouton.text = str(round(self.altitude / 100))
        self.altitudeBouton.rebuild()
        self.speedBouton.text = str(round(self.speedTAS / 10))
        self.speedBouton.rebuild()
        self.etiquetteContainer.rebuild()
        self.etiquetteContainer.update_containing_rect_position()

        # altitude evo

        self.altitudeEvoTxtDis.text = self.altitudeEvoTxt
        self.altitudeEvoTxtDis.rebuild()

        # Vrai dessin

        if self.warning:
            color = (255, 120, 60)
        elif self.part:
            color = (30, 144, 255)
        else:
            if self.plotType == 'arrivee':
                color = (135, 206, 235)
            elif self.plotType == 'depart':
                color = (171, 75, 82)
            else:
                color = (255, 255, 255)

        if self.plotType == 'arrivee':
            pygame.draw.polygon(win, color,
                                ((self.affX + self.size + int(plotSize), self.affY + self.size + int(plotSize)),
                                 (self.affX + self.size - int(plotSize), self.affY + self.size + plotSize),
                                 (self.affX + self.size, self.affY + self.size - plotSize)), 1)
        elif self.plotType == 'depart':
            pygame.draw.rect(win, color, (self.affX, self.affY, self.size * 2, self.size * 2), 1)
        else:
            pygame.draw.rect(win, color, (self.affX, self.affY, self.size * 2, self.size * 2), 1)

        if vecteurs or self.warning:
            pygame.draw.line(win, color, (self.affX + self.size, self.affY + self.size), (
                self.affX + self.size + self.speed * 60 / radarRefresh * vecteurSetting * zoom * math.cos(
                    self.headingRad),
                self.affY + self.size + self.speed * 60 / radarRefresh * vecteurSetting * zoom * math.sin(
                    self.headingRad)), 1)
            for i in range(1, vecteurSetting + 1):
                pygame.draw.circle(win, color, (self.affX + self.size +
                                                self.speed * 60 / radarRefresh * i * zoom * math.cos(self.headingRad),
                                                self.affY + self.size +
                                                self.speed * 60 / radarRefresh * i * zoom * math.sin(self.headingRad)),
                                   2)
        radius = 1
        for plot in self.comete:
            affPlot = [(plot[0] - self.size) * zoom + self.size + scroll[0],
                       (plot[1] - self.size) * zoom + self.size + scroll[1]]
            pygame.draw.circle(win, color, affPlot, int(round(radius)), 1)
            radius += 0.7
        pygame.draw.line(win, (255, 255, 255), (self.affX + self.size, self.affY + self.size),
                         (self.etiquetteX, self.etiquetteY))

        # PART
        if self.part:
            self.indicatifBouton.select()
        else:
            self.indicatifBouton.unselect()

    def drawPilote(self, win, zoom, scroll, vecteurs, vecteurSetting, typeAff):
        # updates
        self.affX = self.x * zoom + scroll[0]
        self.affY = self.y * zoom + scroll[1]

        # on regarde si le bouton est actif pour décaler les suivants sur la ligne

        if self.STCA and not self.STCAlabel.visible:
            self.STCAlabel.show()
            self.typeBouton.set_relative_position(
                (self.typeBouton.get_relative_rect()[0] + self.STCAlabel.get_abs_rect()[2], 0))
        elif not self.STCA and self.STCAlabel.visible:
            self.STCAlabel.hide()
            self.typeBouton.set_relative_position(
                (self.typeBouton.get_relative_rect()[0] - self.STCAlabel.get_abs_rect()[2], 0))

        if self.montrerBouton.visible:
            self.montrerBouton.hide()

        if self.flightLVLbouton.visible:
            self.flightLVLbouton.hide()

        # calcul de la largeur de l'etiquette
        largeur = 0
        for ligne in self.etiquetteList:
            largeurLigne = 0
            for element in ligne:
                if element.visible:
                    largeurLigne += element.get_abs_rect().size[0] + 2
            if largeur < largeurLigne:
                largeur = largeurLigne
        self.etiquetteContainer.rect[2] = largeur

        value = 60  # distance de l'etiquette par rapport au plot

        if self.etiquettePos % 4 == 0:
            self.etiquetteX = self.affX + self.size + value
            self.etiquetteY = self.affY + self.size - value
            self.etiquetteContainer.relative_rect = pygame.Rect(
                (self.etiquetteX, self.etiquetteY - self.etiquetteContainer.rect[3]), (-1, -1))
        elif self.etiquettePos % 4 == 1:
            self.etiquetteX = self.affX + self.size + value
            self.etiquetteY = self.affY + self.size + value
            self.etiquetteContainer.relative_rect = pygame.Rect((self.etiquetteX, self.etiquetteY), (-1, -1))
        elif self.etiquettePos % 4 == 2:
            self.etiquetteX = self.affX + self.size - value
            self.etiquetteY = self.affY + self.size + value
            self.etiquetteContainer.relative_rect = pygame.Rect(
                (self.etiquetteX - self.etiquetteContainer.rect[2], self.etiquetteY), (-1, -1))
        else:
            self.etiquetteX = self.affX + self.size - value
            self.etiquetteY = self.affY + self.size - value
            self.etiquetteContainer.relative_rect = pygame.Rect(
                (self.etiquetteX - self.etiquetteContainer.rect[2], self.etiquetteY - self.etiquetteContainer.rect[3]),
                (-1, -1))
        self.altitudeBouton.text = str(round(self.altitude / 100))
        self.altitudeBouton.rebuild()
        self.speedBouton.text = str(round(self.speedTAS/10))
        self.speedBouton.rebuild()
        self.etiquetteContainer.rebuild()
        self.etiquetteContainer.update_containing_rect_position()

        # altitude evo
        self.altitudeEvoTxtDis.text = self.altitudeEvoTxt
        self.altitudeEvoTxtDis.rebuild()

        # Vrai dessin
        if self.onFrequency:
            color = (0, 255, 0)
        else:
            color = (204, 85, 0)

        if vecteurs:
            pygame.draw.rect(win, color, (self.affX, self.affY, self.size * 2, self.size * 2), 1)
            pygame.draw.line(win, color, (self.affX + self.size, self.affY + self.size), (
                self.affX + self.size + self.speed * 60 / radarRefresh * vecteurSetting * zoom * math.cos(
                    self.headingRad),
                self.affY + self.size + self.speed * 60 / radarRefresh * vecteurSetting * zoom * math.sin(
                    self.headingRad)), 1)
            for i in range(1, vecteurSetting + 1):
                pygame.draw.circle(win, color, (self.affX + self.size +
                                                self.speed * 60 / radarRefresh * i * zoom * math.cos(self.headingRad),
                                                self.affY + self.size +
                                                self.speed * 60 / radarRefresh * i * zoom * math.sin(self.headingRad)),
                                   2)
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

        if self.STCA:
            self.STCAlabel.show()
            self.typeBouton.set_relative_position((self.STCAlabel.get_abs_rect()[2] + 2, 0))
        else:
            self.STCAlabel.hide()
            self.typeBouton.set_relative_position((0, 0))

    def update(self, Papa, zoom, scroll):
        self.heading = Papa.heading
        self.headingRad = Papa.headingRad
        self.indicatif = Papa.indicatif
        self.x = Papa.x
        self.y = Papa.y
        self.comete = Papa.comete
        self.speedIAS = Papa.speedIAS
        self.speedTAS = Papa.speedTAS
        self.speed = Papa.speed

        self.altitude = Papa.altitude
        self.altitudeEvoTxt = Papa.altitudeEvoTxt

        # Radar display
        self.warning = Papa.warning
        self.part = Papa.part
        self.coordination = Papa.coordination
        self.STCA = Papa.STCA
        self.FLInterro = Papa.FLInterro
        self.montrer = Papa.montrer
        self.plotType = Papa.plotType

        # Coord
        if self.coordination == 2:
            self.sortieBouton.select()
            self.sortieBouton.enable()
        elif self.coordination == 1:
            self.sortieBouton.disable()

        else:
            self.typeBouton.text = self.aircraft
        self.typeBouton.rebuild()
        # zoom & scroll

        self.affX = self.x * zoom + scroll[0]
        self.affY = self.y * zoom + scroll[1]

        # ROUTE
        self.route = Papa.route
        self.nextRouteListe = Papa.nextRouteListe
        self.PFL = Papa.PFL

        # TARGETS and spd for altitude/heading etc...
        self.targetFL = Papa.targetFL
        self.targetHeading = Papa.targetHeading

        # bouton
        self.bouton.rect = pygame.Rect((self.affX, self.affY), (20, 20))
        self.bouton.rebuild()
        self.PFLbouton.text = str(Papa.PFL)
        self.PFLbouton.rebuild()
        self.altitudeEvoTxtDis.text = Papa.altitudeEvoTxt

        self.bouton.rect = pygame.Rect((self.affX, self.affY), (20, 20))
        self.bouton.rebuild()

    def etiquetteGen(self, manager):

        # liste des lignes de l'etiquette avec les éléments, pour calculer la largeur
        global etiquetteLines
        self.etiquetteList = []
        for i in range(etiquetteLines):
            self.etiquetteList.append([])

        # conteneur UI pygameUI pour tout foutre dedans
        self.etiquetteContainer = pygame_gui.core.ui_container.UIContainer(pygame.Rect((0, 0), (0, 68)),
                                                                           manager=manager)

        self.speedBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, 17)), text=str(round(self.speedTAS/10)),
            container=self.etiquetteContainer, object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[0].append(self.speedBouton)

        self.STCAlabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((2, 0), (-1, 17)), text='ALRT',
                                                     container=self.etiquetteContainer,
                                                     anchors={'left': 'left', 'left_target': self.speedBouton},
                                                     object_id=pygame_gui.core.ObjectID('@etiquette', 'STCA'))
        self.etiquetteList[0].append(self.STCAlabel)
        self.STCAlabel.hide()

        self.typeBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((2, 0), (-1, 17)), text=self.aircraft,
            container=self.etiquetteContainer, anchors={'left': 'left', 'left_target': self.speedBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[0].append(self.typeBouton)
        self.typeBouton.hide()  # on le cache car le code pense qu'il est caché par défaut, pour les positions des suivants

        self.montrerBouton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((2, 0), (-1, 17)), text='Montrer',
                                                          container=self.etiquetteContainer,
                                                          anchors={'left': 'left', 'left_target': self.speedBouton},
                                                          object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[0].append(self.montrerBouton)
        self.montrerBouton.hide()

        self.flightLVLbouton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((2, 0), (-1, 17)), text='FL?',
                                                            container=self.etiquetteContainer,
                                                            anchors={'left': 'left', 'left_target': self.speedBouton},
                                                            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[0].append(self.flightLVLbouton)
        self.flightLVLbouton.hide()

        self.indicatifBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, 17)), text=str(self.indicatif),
            container=self.etiquetteContainer, anchors={'top': 'top', 'top_target': self.speedBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[1].append(self.indicatifBouton)

        self.altitudeBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (30, 18)), text=str(self.altitude),
            container=self.etiquetteContainer, anchors={'top': 'top', 'top_target': self.indicatifBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[2].append(self.altitudeBouton)

        self.altitudeEvoTxtDis = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((2, 0), (10, 17)), text='-',
                                                             container=self.etiquetteContainer,
                                                             anchors={'left': 'left',
                                                                      'left_target': self.altitudeBouton,
                                                                      'top': 'top',
                                                                      'top_target': self.indicatifBouton},
                                                             object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[2].append(self.altitudeEvoTxtDis)

        self.routeBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, 17)), text=self.last,
            container=self.etiquetteContainer, anchors={'top': 'top', 'top_target': self.altitudeBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[3].append(self.routeBouton)

        self.PFLbouton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((1, 0), (28, 17)), text=str(self.PFL),
                                                      container=self.etiquetteContainer, anchors={'left': 'left',
                                                                                                  'left_target': self.routeBouton,
                                                                                                  'top': 'top',
                                                                                                  'top_target': self.altitudeBouton},
                                                      object_id=pygame_gui.core.ObjectID('@etiquette', 'autre'))
        self.etiquetteList[3].append(self.PFLbouton)

        self.sortieBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (-1, 17)), text=self.sortie,
            container=self.etiquetteContainer, anchors={'left': 'left',
                                                        'left_target': self.PFLbouton, 'top': 'top',
                                                        'top_target': self.altitudeBouton},
            object_id=pygame_gui.core.ObjectID('@etiquette', 'coordBleue'))
        self.etiquetteList[3].append(self.sortieBouton)

        # click gauche, droit et molette sur l'indicatif
        self.indicatifBouton.generate_click_events_from: Iterable[int] = frozenset(
            [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])
        self.etiquetteContainer.rebuild()

    def kill(self):
        self.bouton.kill()
        self.etiquetteContainer.kill()

class NouvelAvionWindow:

    def __init__(self, routes, avions):
        self.routesFull = routes  # on s'en sert que pour avoir les valeurs de spawn/last au moment de l'apparition
        self.routes = routes
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
            text=self.routes[0][0],
            container=self.scrollRoutes))

        for route in self.routes[1:]:
            self.routesBoutons.append(pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (200, 17)),
                text=route[0],
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


