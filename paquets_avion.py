from geometry import *

radarRefresh = 4  # temps en s pour le refresh radar
heureEnRefresh = radarRefresh / 3600  # pour calculer la vitesse des avions (conversion par heure en par refresh)
etiquetteLines = 4
nmToFeet = 6076
altiDefault = 24000  # alti en pied par défault, si on ne rentre pas d'alti pour spawn un avion
acceldefault = 3  # accélération/decelération de kt par refresh
turnRateDefault = 10  # turnrate/refresh par défault

class Game:
    def __init__(self, heure):
        self.ready = False
        self.paused = True
        self.heure = heure


class Packet:
    def __init__(self, Id, game=None, dictAvions=None, requests=None, map=None, perfos=None):
        self.Id = Id
        self.game = game
        self.dictAvions = dictAvions
        self.requests = requests
        self.map = map
        self.perfos = perfos


class AvionPacket:
    global heureEnRefresh

    def __init__(self, gameMap, Id, indicatif, aircraft, perfos, route, FL=None, x=None, y=None, heading=None, PFL=None):

        self.Id = Id
        self.indicatif = indicatif
        self.aircraft = aircraft
        
        if x is not None:  # si on a défini un point de spawn pendant le setup
            self.x = x
            self.y = y
            
        else:  # s'il n'y a pas de point de spawn défini, on prend le 1er point de la route
            self.x = gameMap['points'][route['points'][0]['name']][0]
            self.y = gameMap['points'][route['points'][0]['name']][1]

        self.comete = []

        if FL is not None:  # si on a défini un FL pendant le setup
            self.altitude = FL * 100  # en pieds
        else:
            self.altitude = altiDefault

        self.speedIAS = perfos['IAS']
        self.speedGS = self.speedIAS + self.altitude / 200  # la GS dépends de l'alti
        self.speedPx = self.speedGS / gameMap['mapScale'] * heureEnRefresh

        # RADAR display
        self.warning = False
        self.part = False
        self.STCA = False
        self.FLInterro = False
        self.montrer = False

        # perfo
        self.turnRate = turnRateDefault
        self.maxROC = perfos['ROC'] / 60 * radarRefresh  # on transforme pied/min en pied/refresh radar
        self.maxROD = perfos['ROD'] / 60 * radarRefresh
        
        # altis
        self.evolution = 0  # taux de variation/radar refresh
        self.altitudeEvoTxt = '-'

        # format route {nomRoute, routeType, listeRoutePoints, sortie} points : {caractéristiques eg : nom alti IAS}
        self.route = route

        if PFL is not None:
            self.PFL = PFL
        else:
            self.PFL = FL

        self.headingMode = False
        self.intercept = False
        self.axe = None

        if calculateDistance(self.x, self.y, gameMap['points'][self.route['points'][0]['name']][0],
                             gameMap['points'][self.route['points'][0]['name']][1]) <= 4 * self.speedPx:
            self.nextPoint = self.route['points'][1]
        else:
            self.nextPoint = self.route['points'][0]

        if route['sortie']:
            self.sortie = route['sortie'][0]
        else:
            self.nextRoute = 'bye'
            self.sortie = 'decollage'

        # heading
        if heading is not None:
            self.heading = heading
        else:  # points format {name: (x, y, balise)}
            self.heading = calculateHeading(self.x, self.y, gameMap['points'][self.nextPoint['name']][0],
                                            gameMap['points'][self.nextPoint['name']][1])
        self.headingRad = (self.heading - 90) / 180 * math.pi

        # selected 
        self.selectedAlti = self.altitude
        self.selectedHeading = self.heading
        self.selectedIAS = self.speedIAS
       
    def updateAlti(self):
        
        if self.altitude != self.selectedAlti:  # on regarde s'il faut évoluer
            
            if self.altitude - self.selectedAlti > 0:               
                if abs(self.altitude - self.selectedAlti) <= abs(self.evolution):  # on arrive dans moins d'un refresh ?
                    self.altitude = self.selectedAlti  # alors, on met le niveau cible
                else:
                    self.altitude += self.evolution  # sinon, on descend juste au taux sélecté
                    self.altitudeEvoTxt = '↘'
                    
            else:
                if abs(self.altitude - self.selectedAlti) <= abs(self.evolution):  # on arrive dans moins d'un refresh ?
                    self.altitude = self.selectedAlti  # alors, on met le niveau cible
                else:
                    self.altitude += self.evolution  # sinon, on monte au taux sélecté
                    self.altitudeEvoTxt = '↗'
                    
        else:  # si on n'évolue pas, on met ce texte
            self.altitudeEvoTxt = '-'

    def move(self, gameMap):
        
        # heading update
        if not self.headingMode:  # si l'avion est en direct et pas en cap
            
            if math.sqrt((self.x - gameMap['points'][self.nextPoint['name']][0]) ** 2 + (
                    self.y - gameMap['points'][self.nextPoint['name']][1]) ** 2) <= 2 * self.speedPx:  # si on est proche point

                if self.nextPoint == self.route['points'][-1]:  # si on est arrivé au bout de la route
                    return True  # le return True permet au serveur de supprimer l'avion
                else:
                    # on passe au point suivant dans la liste
                    self.nextPoint = self.route['points'][self.route['points'].index(self.nextPoint) + 1]

            self.selectedHeading = calculateHeading(self.x, self.y, gameMap['points'][self.nextPoint['name']][0],
                                                    gameMap['points'][self.nextPoint['name']][1])

        if self.heading != self.selectedHeading:
            if abs(self.heading - self.selectedHeading) <= self.turnRate:
                self.heading = self.selectedHeading
            elif abs(self.heading - self.selectedHeading) > 180:
                self.heading = (self.heading + self.turnRate * (self.heading - self.selectedHeading) / abs(
                    self.heading - self.selectedHeading)) % 360
            else:
                self.heading -= self.turnRate * (self.heading - self.selectedHeading) / abs(
                    self.heading - self.selectedHeading)

        self.headingRad = (self.heading - 90) / 180 * math.pi

        # comete
        if len(self.comete) >= 6:  # si la comète est de taille max, on enlève le premier point, le + vieux
            self.comete = self.comete[1:6]
        self.comete.append((self.x, self.y))

        self.updateAlti()  # on change le niveau de l'avion si on est en evolution

        if self.speedIAS != self.selectedIAS:  # s'il faut accélérer ou ralentir
            # on change la vitesse par un pas d'accél/deccel défaut
            self.speedIAS += (self.selectedIAS - self.speedIAS)/abs(self.selectedIAS - self.speedIAS) * acceldefault

        self.speedGS = self.speedIAS + self.altitude / 200
        self.speedPx = self.speedGS / gameMap['mapScale'] * heureEnRefresh  # on convertit les kt en px/refresh

        # mouvement 
        self.x += self.speedPx * math.cos(self.headingRad)
        self.y += self.speedPx * math.sin(self.headingRad)

# format map : [points, secteurs, segments, routes, mapScale, axes, zones]
