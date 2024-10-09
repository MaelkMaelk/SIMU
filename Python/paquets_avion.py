import math
# Native imports
import random

# Imports fichiers
from Python.geometry import *
from Python.valeurs_config import *
import Python.vitesses as vitesses


class Game:
    def __init__(self, heure):
        self.ready = False
        self.paused = False  # on commence avec la situation en pause
        self.heure = heure


class Packet:
    def __init__(self, Id, game=None, dictAvions=None, requests=None, carte=None, perfos=None):
        self.Id = Id
        self.game = game
        self.dictAvions = dictAvions
        self.requests = requests
        self.map = carte
        self.perfos = perfos


class AvionPacket:

    def __init__(self, gameMap, Id, indicatif, aircraft, perfos, route, arrival, FL=None, x=None, y=None, heading=None,
                 PFL=None, medevac=False):

        self.Id = Id
        self.indicatif = indicatif
        self.aircraft = aircraft
        self.arrival = arrival and (route['arrival'] != False)
        
        if x is not None:  # si on a défini un point de spawn pendant le setup
            self.x = x
            self.y = y
            
        else:  # s'il n'y a pas de point de spawn défini, on prend le 1er point de la route
            self.x = gameMap['points'][route['points'][0]['name']][0]
            self.y = gameMap['points'][route['points'][0]['name']][1]

        self.comete = []

        # altis
        if FL is not None:  # si on a défini un FL pendant le setup
            self.altitude = FL * 100  # en pieds
        elif 'FL' in route['points'][0]:  # si on a une alti de spawn
            self.altitude = route['points'][0]['FL'] * 100
        else:
            self.altitude = altiDefault

        self.evolution = 0  # taux de variation/radar refresh
        self.altitudeEvoTxt = '-'

        # RADAR display
        self.warning = False
        self.STCA = False
        self.montrer = False
        # états possibles : previousFreq, previousShoot, inFreq, nextCoord, nextShoot, nextFreq
        self.etatFrequence = "previousFreq"
        self.integreOrganique = False  # si on doit ou non afficher la case d'intégration organique
        self.boutonsHighlight = []
        self.modeA = str(random.randint(1000, 9999))

        if medevac:
            self.medevac = 'MEDEVAC'  # TODO ajouter le noW
        else:
            self.medevac = ''

        if indicatif[:2] in gameMap['callsigns']:
            self.callsignFreq = gameMap['callsigns'][indicatif[:2]]
        elif indicatif[:3] in gameMap['callsigns']:
            self.callsignFreq = gameMap['callsigns'][indicatif[:3]]
        else:
            self.callsignFreq = 'caca'

        if route['type'] == 'DEPART':
            self.provenance = route['provenance']
        else:
            self.provenance = random.choice(gameMap['aeroports'][route['provenance']])

        if self.arrival:
            self.destination = route['arrival']['aeroport']
        else:
            self.destination = random.choice(gameMap['aeroports'][route['destination']])

        # format route {nomRoute, routeType, listeRoutePoints, sortie} points : {caractéristiques eg : nom alti IAS}
        self.route = route

        self.headingMode = False

        self.nextPoint = None
        self.findNextPoint(gameMap)

        if PFL is not None:
            self.PFL = PFL
        elif gameMap['floor'] < self.altitude/100 < gameMap['ceiling']:
            self.PFL = int(self.altitude / 100)
        else:
            self.PFL = 300

        self.DCT = self.nextPoint['name']

        # On détermine le prochain secteur et le XFL en fonction du PFL, et si c'est une arrivée
        self.nextSector = None
        self.defaultXPT = route['XPT']  # le XPT par default
        self.XPT = self.defaultXPT
        self.EPT = route['EPT']

        if self.arrival:  # si c'est une arrivée,
            self.XFL = route['arrival']['XFL']
            self.nextSector = route['arrival']['secteur']

        else:
            if gameMap['floor'] < self.PFL < gameMap['ceiling']:
                self.XFL = self.PFL
            elif self.PFL > gameMap["ceiling"]:
                self.XFL = 360
            else:
                self.XFL = 300

            for sortie in self.route['sortie']:
                if sortie['min'] < self.PFL < sortie['max']:
                    self.nextSector = sortie['name']

        if not self.nextSector:  # si on n'a pas réussi à mettre un secteur suivant, on met un défaut pour pas crash
            self.nextSector = secteurDefault

        self.nextFrequency = gameMap['secteurs'][self.nextSector]['frequence']
        self.etranger = gameMap['secteurs'][self.nextSector]['etranger']

        self.CFL = None

        for point in route['points'][route['points'].index(self.nextPoint):]:
            if 'EFL' in point:
                self.CFL = point['EFL']
        if not self.CFL:
            self.CFL = round(self.altitude / 100)

        # heading
        if heading is not None:
            self.heading = heading
        else:  # points format {name: (x, y, balise)}
            self.heading = calculateHeading(self.x, self.y, gameMap['points'][self.nextPoint['name']][0],
                                            gameMap['points'][self.nextPoint['name']][1])
        self.headingRad = (self.heading - 90) / 180 * math.pi

        # perfo
        self.turnRate = turnRateDefault
        self.perfos = perfos
        self.forcedSpeed = False
        self.forcedEvo = False
        self.machMode = False
        self.changeSpeed()

        # selected + vitesses
        if self.machMode:
            self.selectedIAS = self.perfos['descentIAS']
            self.mach = self.selectedMach
            self.speedTAS = vitesses.mach_to_TAS(self.mach, self.altitude)
            self.speedIAS = vitesses.TAS_to_IAS(self.speedTAS, self.altitude)
        else:
            self.speedIAS = self.selectedIAS
            self.mach = vitesses.IAS_to_Mach(self.speedIAS, self.altitude)
            self.speedTAS = vitesses.mach_to_TAS(self.mach, self.altitude)

        self.speedGS = self.speedTAS

        self.selectedAlti = self.CFL * 100
        self.selectedHeading = self.heading
        self.selectedMach = self.mach
        self.clearedIAS = None
        self.clearedMach = None
        self.clearedHeading = None
        self.clearedRate = None
        self.clearedMachMode = False
        self.clearedIASMode = False

        self.speedPx = self.speedGS / gameMap['mapScale'] * heureEnRefresh

    def findNextPoint(self, carte):

        self.nextPoint = findClosestSegment(self.route['points'], (self.x, self.y), carte['points'])[1]
        self.DCT = self.nextPoint['name']

    def changeXFL(self, carte) -> None:
        """
        Change le XFL en fonction du PFL. À utliser quand le PFL change
        :return:
        """
        if self.PFL > 365 and not self.arrival:
            self.nextSector = "RU"
            self.XFL = 360
        elif not self.arrival:
            self.XFL = self.PFL
            self.changeSortieSecteur(carte)

    def changeSortieSecteur(self, carte) -> None:
        """
        Change le secteur de sortie. À utiliser quand le XFL change
        :return:
        """

        for sortie in self.route['sortie']:
            if sortie['min'] < self.XFL < sortie['max']:
                self.nextSector = sortie['name']
                break
        self.etranger = carte['secteurs'][self.nextSector]['etranger']
        self.nextFrequency = carte['secteurs'][self.nextSector]['frequence']

    def updateEtatFreq(self, nouvelEtat=None) -> None:
        """
        Fonction qui met à jour l'état fréquence de l'avion. S'il n'y a pas de param spécifié, on passe juste au suivant
        :param nouvelEtat: Le nouvel état fréquence de l'avion
        :return:
        """

        if nouvelEtat:
            self.etatFrequence = nouvelEtat
        else:
            i = liste_etat_freq.index(self.etatFrequence)
            if i != len(liste_etat_freq) - 1:  # on vérifie que ce n'est pas le dernier état fréquence
                if self.etranger and self.etatFrequence == 'nextCoord':
                    i += 1
                self.etatFrequence = liste_etat_freq[i + 1]
       
    def updateAlti(self):
        
        if self.altitude != self.selectedAlti:  # on regarde s'il faut évoluer
            
            if self.altitude - self.selectedAlti > 0:

                # on arrive dans moins d'un refresh ?
                if abs(self.altitude - self.selectedAlti) <= abs(self.evolution / 60 * radarRefresh):
                    self.altitude = self.selectedAlti  # alors, on met le niveau cible
                else:
                    self.altitude += self.evolution / 60 * radarRefresh  # sinon, on descend juste au taux sélecté
                    self.altitudeEvoTxt = '↓'
                    
            else:
                # on arrive dans moins d'un refresh ?
                if abs(self.altitude - self.selectedAlti) <= abs(self.evolution / 60 * radarRefresh):
                    self.altitude = self.selectedAlti  # alors, on met le niveau cible
                else:
                    self.altitude += self.evolution / 60 * radarRefresh  # sinon, on monte au taux sélecté
                    self.altitudeEvoTxt = '↑'
                    
        else:  # si on n'évolue pas, on met ce texte
            self.altitudeEvoTxt = '-'
            self.evolution = 0

    def changeEvolution(self) -> None:
        """
        Sélectionne la vitesse en fonction de la phase de vol
        :return:
        """

        if self.forcedEvo:
            return None

        if self.altitude >= altitude_conversion:
            # ici, on prend les perfos en croisière

            if self.selectedAlti < self.altitude:
                self.evolution = - self.perfos['cruiseROD']

            else:
                self.evolution = self.perfos['cruiseROC']

        elif self.altitude >= altitude_cruise:
            # ici, on regarde si on est en montée/descente ou alors, si on approche du niveau de croisière

            if self.selectedAlti < self.altitude:
                self.evolution = - self.perfos['cruiseROD']

            else:
                self.evolution = self.perfos['climbROC']

        else:
            # ici, on est dans les basses couches donc on prend les perfos en basse alti

            if self.selectedAlti < self.altitude:
                self.evolution = - self.perfos['descentROD']

            else:
                self.evolution = self.perfos['initialClimbROC']

    def move(self, gameMap):

        # frequence update
        if self.etatFrequence == 'inFreq':

            if self.calculeEstimate(gameMap['points'], self.XPT) <= 60 * valeurCoord:  # si on sort dans moins de 6min
                self.updateEtatFreq()
        
        # heading update
        if not self.headingMode:  # si l'avion est en direct et pas en cap
            
            if math.sqrt((self.x - gameMap['points'][self.nextPoint['name']][0]) ** 2 + (
                    self.y - gameMap['points'][self.nextPoint['name']][1]) ** 2) <= 2 * self.speedPx:  # si on est proche point

                if self.nextPoint == self.route['points'][-1]:  # si on est arrivé au bout de la route
                    return True  # le return True permet au serveur de supprimer l'avion
                else:
                    # on passe au point suivant dans la liste
                    ancien = self.nextPoint  # pour la comparaison après
                    self.nextPoint = self.route['points'][self.route['points'].index(self.nextPoint) + 1]
                    if ancien['name'] == self.DCT:  # si le point clairé est celui qu'on passe
                        self.DCT = self.nextPoint['name']  # alors, on passe au point suivant aussi

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
        if len(self.comete) >= 9:  # si la comète est de taille max, on enlève le premier point, le + vieux
            self.comete = self.comete[1:9]
        self.comete.append((self.x, self.y))

        self.changeEvolution()
        self.updateAlti()  # on change le niveau de l'avion si on est en evolution

        self.changeSpeed()
        self.computeSpeed()

        self.speedPx = self.speedGS / gameMap['mapScale'] * heureEnRefresh  # on convertit les kt en px/refresh

        # mouvement 
        self.x += self.speedPx * math.cos(self.headingRad)
        self.y += self.speedPx * math.sin(self.headingRad)

    def computeSpeed(self):

        """
        Fait évoluer la vitesse si on a besoin
        :return:
        """

        if not self.machMode:
            if self.speedIAS != self.selectedIAS:  # s'il faut accélérer ou ralentir
                # on change la vitesse par un pas d'accél/deccel défaut
                if abs(self.selectedIAS - self.speedIAS) <= acceldefault:
                    self.speedIAS = self.selectedIAS
                else:
                    self.speedIAS += (self.selectedIAS - self.speedIAS)/abs(self.selectedIAS - self.speedIAS) * acceldefault

            self.mach = vitesses.IAS_to_Mach(self.speedIAS, self.altitude)
        else:
            if self.mach != self.selectedMach:
                # on change la vitesse par un pas d'accél/deccel défaut
                if abs(self.selectedMach - self.mach) <= acceldefaultMach:
                    self.mach = self.selectedMach
                else:
                    self.mach += (self.selectedMach - self.mach) / abs(self.selectedMach - self.mach) * acceldefaultMach

            self.speedIAS = vitesses.TAS_to_IAS(self.speedTAS, self.altitude)

        self.speedTAS = vitesses.mach_to_TAS(self.mach, self.altitude)
        self.speedGS = self.speedTAS

    def changeSpeed(self) -> None:
        """
        Sélectionne la vitesse en fonction de la phase de vol
        :return:
        """

        self.machMode = False
        if self.forcedSpeed:
            if self.altitude >= altitude_conversion:  # au-dessus de l'alti de conversion tout se fera en mach

                self.machMode = True
            return None

        if self.altitude >= altitude_conversion:  # au-dessus de l'alti de conversion tout se fera en mach

            self.machMode = True

            if self.evolution == 0:
                self.selectedMach = self.perfos['cruiseMach']

            elif self.evolution < 0:
                self.selectedMach = self.perfos['descentMach']

            else:
                self.selectedMach = self.perfos['climbMach']

        elif self.altitude >= altitude_cruise:  # en-dessous de l'alti de conversion tout se fera en IAS
            # ici, on regarde si on est en montée/descente initiale ou alors, si on approche du niveau de croisière

            if self.evolution <= 0:  # on prend les perfs de descente pour la croisière (pas trouvé de perfo IAS cruise)
                self.selectedIAS = self.perfos['descentIAS']

            else:
                self.selectedIAS = self.perfos['climbIAS']

        else:
            # ici, on est dans les basses couches donc on prend les perfos en basse alti

            if self.evolution <= 0:
                self.selectedIAS = self.perfos['descentIAS']
                # les perfos sont les mêmes pendant la majorité de la descente d'où le manque de 240

            else:
                self.selectedIAS = self.perfos['initialClimbIAS']

    def calculeEstimate(self, points: dict, pointVoulu: str) -> float:
        """
        Calcule le temps à un point sur notre route. Pour avoir l'estimée, il faudra rajouter l'heure courante
        :param points: dict des points de la carte
        :param pointVoulu: le nom du point pour lequel on veut l'estimée
        :return:
        """
        distance = 0
        x1 = self.x
        y1 = self.y

        for point in self.route['points']:
            if point['name'] == self.DCT:
                break

        debut = self.route['points'].index(point)

        for point in self.route['points'][debut:]:  # on compte à partir du prochain point connu par le système

            x2 = points[point['name']][0]
            y2 = points[point['name']][1]

            distance += calculateDistance(x1, y1, x2, y2)

            if point['name'] == pointVoulu:
                break

            x1 = x2
            y1 = y2

        return distance / (self.speedPx / heureEnRefresh) * 3600
