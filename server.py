import socket
import sys
from _thread import *
from queue import Queue
from network import MCAST_GRP, MCAST_PORT, port
from paquets_avion import *
import pickle
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import struct
import platform

SIMU = 'simu.xml'
mode_ecriture = True

# On se connecte à internet pour avoir notre adresse IP locale... Oui oui
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(("8.8.8.8", 80))
servername = input('Nom du serveur:')
server_ip = sock.getsockname()[0]
sock.close()

# fini on ferme le socket

print(servername, server_ip)

if platform.system() == 'Windows':  # on vérifie pour faire marcher le Mcast sur windows
    mcast_group = ''
else:
    mcast_group = MCAST_GRP  # on prend celui de network si on est sur linux

# set up le socket pour le UDP, il répond au scan server coté client
pingSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
pingSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
pingSock.bind((mcast_group, MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
pingSock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# socket TCP pour les connecter avec les clients
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((server_ip, port))
except socket.error as e:
    str(e)

s.listen(2)

playerId = 0
dictAvion = {}  # dict contenant tous les avions
requests = []  # liste des requêtes que le serveur doit gérer
segments = {}
gameMap = {'points': {}, 'secteurs': [], 'segments': [], 'routes': {}, 'mapScale': 0}

# XML map loading

tree = ET.parse('XML/mapAPS.xml')
root = tree.getroot()
mapScale = float(root.find('scale').text)  # conversion nm-px

gameMap.update({"ceiling": int(root.find('ceiling').text)})  # on récupère plancher et plafond
gameMap.update({"floor": int(root.find('floor').text)})

for point in root.find('points'):  # on parcourt la liste xml de points
    name = point.attrib['name']
    x = int(point.find('x').text)
    y = int(point.find('y').text)

    if point.find('invisible'):  # on regarde si le champ balise est présent
        balise = bool(point.find('invisible').text)  # on ajoute sa valeur
    else:
        balise = False

    gameMap['points'].update({name: (x, y, balise)})

for secteur in root.find('secteurs'):

    contour = []  # liste des points délimitant le contour du secteur, dans l'ordre de lecture xml

    for limite in secteur.findall('limite'):
        x = int(limite.find('x').text)
        y = int(limite.find('y').text)
        contour.append((x, y))

    gameMap['secteurs'].append({'couleur': [int(x) for x in secteur.attrib['color'].split(',')], 'contour': contour})

listeAeroports = {}

for direction in root.find('Aeroports'):
    liste_de_cette_direction = []

    for aeroport in direction:
        liste_de_cette_direction.append(aeroport.text)

    if not liste_de_cette_direction:
        print("[Problème] Il n'y a pas d'aéroports pour la direction", direction.tag)

    listeAeroports.update({direction.tag: liste_de_cette_direction})

gameMap.update({'aeroports': listeAeroports})

# parsing des routes pour conaître tous les types de routes, pour l'affichage des segments

for route in root.find('routes'):
    if route.find('Type').text not in segments:
        segments.update({route.find('Type').text: []})

gameMap['segments'] = segments  # liste des segments de route pour les dessiner qu'une seule fois

for route in root.find('routes'):  # construction des routes
    if 'name' in route.attrib:
        nomRoute = route.attrib['name']
    else:
        nomRoute = route.findall('point')[0].find('name').text + "-" + route.findall('point')[-1].find('name').text
    routeType = route.find('Type').text
    listeSortie = []
    listeRoutePoints = []
    arrival = False
    XPT = route.findall('point')[-1].find('name').text  # on met le dernier point par défaut s'il n'est pas précisé
    EPT = route.findall('point')[1].find('name').text  # on met le 1er point par défaut s'il n'est pas précisé

    x1 = gameMap['points'][route.find('point').find('name').text][0]
    y1 = gameMap['points'][route.find('point').find('name').text][1]

    for point in route.findall('point'):
        pointDict = {}
        pointDict.update({'name': point.find('name').text})

        for XMLpoint in point:
            try:
                XMLpointValue = int(XMLpoint.text)
            except:
                XMLpointValue = XMLpoint.text

                if XMLpoint.tag == 'XPT':
                    XMLpointValue = bool(XMLpoint.text)

                    if XMLpointValue:
                        XPT = point.find('name').text

                if XMLpoint.tag == 'EPT':
                    XMLpointValue = bool(XMLpoint.text)

                    if XMLpointValue:
                        EPT = point.find('name').text

            pointDict.update({XMLpoint.tag: XMLpointValue})

        listeRoutePoints.append(pointDict)

        y2 = gameMap['points'][point.find('name').text][1]
        x2 = gameMap['points'][point.find('name').text][0]
        if ((x1, y1), (x2, y2)) not in gameMap['segments'][routeType] and x1 != x2 and y1 != y2:
            gameMap['segments'][routeType].append(((x1, y1), (x2, y2)))
        x1 = x2
        y1 = y2
    provenance = 'N'
    destination = 'S'
    if routeType == 'DEPART':
        provenance = route.find('AD').text
    elif route.find('provenance') is not None:
        provenance = route.find('provenance').text
    else:
        print('[Problème] pas de direction de provenance pour la route', nomRoute)
        provenance = 'N'

    if route.find('destination') is not None:
        destination = route.find('destination').text
    else:
        print('[Problème] pas de direction de destination pour la route', nomRoute)
        destination = 'S'

    if route.find('arrival') is not None:
        arrival = {'XFL': int(route.find('arrival').text), 'secteur': route.find('arrival').attrib['secteur'], 'aeroport': route.find('arrival').attrib['AD']}
    for sortie in route.findall('sortie'):
        listeSortie.append({'name': sortie.text, 'min': int(sortie.attrib['min']), 'max': int(sortie.attrib['max'])})
    gameMap['routes'].update({nomRoute: {'name': nomRoute,
                                         'type': routeType,
                                         'points': listeRoutePoints,
                                         'sortie': listeSortie,
                                         'arrival': arrival,
                                         'XPT': XPT,
                                         'EPT': EPT,
                                         'provenance': provenance,
                                         'destination': destination}})

gameMap.update({'mapScale': mapScale})

aircraftType = {}
tree = ET.parse('XML/aircrafts.xml')
root = tree.getroot()

for aircraft in root:
    aircraftType.update(
        {aircraft.attrib['name']: {'IAS': int(aircraft.find('speed').text),
                                   'plafond': int(aircraft.find('ceiling').text),
                                   'ROC': int(aircraft.find('ROC').text),
                                   'ROD': int(aircraft.find('ROD').text)}})


try:  # on essaye de charger une simu, si elle existe
    tree = ET.parse('XML/' + SIMU)

    heure = tree.find('heure').text
    heure = int(heure[0:2]) * 3600 + int(heure[2:]) * 60

    avionSpawnListe = []
    for avion in tree.find('avions'):

        avionDict = {}

        for XMLpoint in avion:
            try:
                XMLpointValue = int(XMLpoint.text)
            except:
                XMLpointValue = XMLpoint.text
            avionDict.update({XMLpoint.tag: XMLpointValue})

        heureSpawn = avion.attrib['heure']
        heureSpawn = int(heureSpawn[0:2]) * 3600 + int(heureSpawn[2:]) * 60

        avionSpawnListe.append((heureSpawn, avionDict))
except:  # sinon, on demande juste l'heure de début

    heure = input('Heure de début de simu, format: hhmm')
    heure = int(heure[0:2]) * 3600 + int(heure[2:]) * 60
    avionSpawnListe = []

game = Game(heure)

# XML écriture

SimuTree = ET.Element('simu')
heureXML = ET.SubElement(SimuTree, 'heure')
heureXML.text = '1002'
avionsXML = ET.SubElement(SimuTree, 'avions')


def generateAvionXML(parent, heureEcriture, indicatifEcriture, aircraftEcriture, routeEcriture, altitudeEcriture, xEcriture=None, yEcriture=None, headingEcriture=None, PFLEcriture=None):

    avionXML = ET.SubElement(parent, 'avion')
    avionXML.set('heure', str(heureEcriture))

    node = ET.SubElement(avionXML, 'indicatif')
    node.text = str(indicatifEcriture)
    node = ET.SubElement(avionXML, 'aircraft')
    node.text = str(aircraftEcriture)
    node = ET.SubElement(avionXML, 'route')
    node.text = str(routeEcriture)
    node = ET.SubElement(avionXML, 'altitude')
    node.text = str(altitudeEcriture)
    node = ET.SubElement(avionXML, 'arrival')
    node.text = str(arrival)

    if xEcriture is not None:
        node = ET.SubElement(avionXML, 'x')
        node.text = str(xEcriture)
        node = ET.SubElement(avionXML, 'y')
        node.text = str(yEcriture)

    if headingEcriture is not None:
        node = ET.SubElement(avionXML, 'heading')
        node.text = str(headingEcriture)

    if PFLEcriture is not None:
        node = ET.SubElement(avionXML, 'PFL')
        node.text = str(PFLEcriture)


def threaded_client(conn, caca):
    global dictAvion
    global game
    global map
    global aircraftType
    global playerId

    nombre = 0
    localPlayerId = playerId
    playerId += 1
    packetId = 0
    packet = Packet(packetId, game=game, dictAvions=dictAvion, carte=gameMap, perfos=aircraftType)
    conn.send(pickle.dumps(packet))
    reply = ""
    while True:
        try:
            data = pickle.loads(conn.recv(2048 * 16))
            if packetId != data.Id:
                reqQ.put(data.requests)
                packetId = data.Id
            if not data:
                print("Disconnected")
                break
            else:
                reply = Packet(packetId, game=game, dictAvions=dictAvion)

            conn.sendall(pickle.dumps(reply))
            nombre = 0
        except:
            if nombre >= 200:
                break
            else:
                nombre += 1

    print("Lost connection")
    conn.close()


def threaded_waiting():
    print("Waiting for a connection, Server Started")
    while True:
        conn, addr = s.accept()
        print("Connected to:", addr)
        start_new_thread(threaded_client, (conn, 0))


def threaded_ping_responder():
    global server_ip
    while True:
        # For Python 3, change next line to "print(sock.recv(10240))"
        data, address = pingSock.recvfrom(10240)
        print(data, address)
        if data == b'Server?':
            pingSock.sendto(servername.encode('utf-8'), address)


reqQ = Queue()
start_new_thread(threaded_waiting, ())
start_new_thread(threaded_ping_responder, ())
temps = time.time()
STCAtriggered = False
planeId = 0
accelerationTemporelle = 1
Running = True
while Running:
    inReq = reqQ.get()
    requests.append(inReq)
    for reqSublist in requests:
        for req in reqSublist:  # format requêtes : [Id avion, type requête, data]
            if req[1] == 'Add':
                req[2].Id = planeId
                dictAvion.update({planeId: req[2]})
                planeId += 1
                if mode_ecriture:

                    heures = str(round(game.heure // 3600))
                    if len(heures) == 1:
                        heures = '0' + heures
                    minutes = str(round(game.heure % 3600 // 60))
                    if len(minutes) == 1:
                        minutes = '0' + minutes

                    generateAvionXML(avionsXML,
                                     heures + minutes,
                                     req[2].indicatif,
                                     req[2].aircraft,
                                     req[2].route['name'],
                                     req[2].altitude,
                                     xEcriture=req[2].x,
                                     yEcriture=req[2].y,
                                     PFLEcriture=req[2].PFL)

            elif req[1] == 'Remove':
                dictAvion.pop(req[0])
            elif req[1] == 'Altitude':
                dictAvion[req[0]].selectedAlti = req[2]
            elif req[1] == 'PFL':
                dictAvion[req[0]].PFL = req[2]
                dictAvion[req[0]].changeXFL()
                dictAvion[req[0]].changeSortieSecteur()
            elif req[1] == 'CFL':
                dictAvion[req[0]].CFL = req[2]
            elif req[1] == 'C_IAS':
                if len(req) == 3:
                    dictAvion[req[0]].clearedIAS = req[2]
                else:
                    dictAvion[req[0]].clearedIAS = None
            elif req[1] == 'C_Rate':
                if len(req) == 3:
                    dictAvion[req[0]].clearedRate = req[2]
                else:
                    dictAvion[req[0]].clearedRate = None
            elif req[1] == 'XFL':
                dictAvion[req[0]].XFL = req[2]
                dictAvion[req[0]].changeSortieSecteur()
            elif req[1] == 'XPT':
                dictAvion[req[0]].XPT = req[2]
            elif req[1] == 'HDG':
                dictAvion[req[0]].clearedHeading = req[2]
            elif req[1] == 'Heading':
                dictAvion[req[0]].headingMode = True
                dictAvion[req[0]].selectedHeading = req[2]
            elif req[1] == 'IAS':
                dictAvion[req[0]].selectedIAS = req[2]
            elif req[1] == 'DCT':
                dictAvion[req[0]].clearedHeading = None
                dictAvion[req[0]].DCT = req[2]
            elif req[1] == 'Warning':
                dictAvion[req[0]].warning = not dictAvion[req[0]].warning
            elif req[1] == 'Integre':
                dictAvion[req[0]].integreOrganique = True
            elif req[1] == 'Direct':
                dictAvion[req[0]].headingMode = False
                for point in dictAvion[req[0]].route['points']:
                    if point['name'] == req[2]:
                        dictAvion[req[0]].nextPoint = point
                        break
            elif req[1] == 'Route':
                dictAvion[req[0]].nextRoute = req[2]
                dictAvion[req[0]].changeRoute(gameMap)
            elif req[1] == 'HighlightBouton':
                if req[2] in dictAvion[req[0]].boutonsHighlight:  # si le bouton est déjà highlight alors:
                    dictAvion[req[0]].boutonsHighlight.remove(req[2])
                else:
                    dictAvion[req[0]].boutonsHighlight.append(req[2])
            elif req[1] == 'Montrer':
                dictAvion[req[0]].montrer = not dictAvion[req[0]].montrer
            elif req[1] == 'EtatFreq':
                dictAvion[req[0]].updateEtatFreq(req[2])
            elif req[1] == 'FL?':
                dictAvion[req[0]].FLInterro = not dictAvion[req[0]].FLInterro
            elif req[1] == 'Pause':
                game.paused = not game.paused
            elif req[1] == 'Faster':
                accelerationTemporelle += 0.5
            elif req[1] == 'Slower':
                if accelerationTemporelle > 0.5:
                    accelerationTemporelle -= 0.5
            elif req[1] == 'Save' and mode_ecriture:
                xmlstr = minidom.parseString(ET.tostring(SimuTree)).toprettyxml(indent="   ")
                with open("XML/simu.xml", "w") as f:
                    f.write(xmlstr)

    toBeRemovedFromSpawn = []
    for spawn in avionSpawnListe:
        if spawn[0] <= game.heure:
            for route in gameMap['routes']:
                if route == spawn[1]['route']:
                    spawnRoute = gameMap['routes'][route]
                    break
            if 'altitude' in spawn[1]:
                spawnFL = round(spawn[1]['altitude']/100)
            else:
                spawnFL = None
            dictAvion.update({planeId: AvionPacket(
                gameMap,
                planeId,
                spawn[1]['indicatif'],
                spawn[1]['aircraft'],
                aircraftType[spawn[1]['aircraft']],
                spawnRoute,
                spawn[1]['arrival'] == 'True',
                FL=spawnFL,
                x=spawn[1]['x'],
                y=spawn[1]['y'])})
            toBeRemovedFromSpawn.append(spawn)
            planeId += 1

    for avion in toBeRemovedFromSpawn:
        avionSpawnListe.remove(avion)

    if time.time() - temps >= radarRefresh/accelerationTemporelle and game.paused:
        game.heure += (time.time() - temps) * accelerationTemporelle
        temps = time.time()
        suppListe = []
        for avion in list(dictAvion.values()):
            # si jamais l'avion doit etre supp, il le renvoie à la fin du move, sinon None
            if avion.move(gameMap):
                suppListe.append(avion.Id)
        for avion in suppListe:
            dictAvion.pop(avion)
        for avion in list(dictAvion.values()):
            # tous les calculs de distances sont ici effectués en pixel, la conversion se fait avec le mapScale
            # TODO remplacer ce STCA avec le nouveau dans server_def
            STCAtriggered = False
            predictedPos = []
            VspeedOne = avion.evolution
            AltitudeOne = avion.altitude
            for i in range(12):
                predictedPos.append((avion.x + avion.speedGS * 15 / radarRefresh * (i + 1) * math.cos(avion.headingRad),
                                     avion.y + avion.speedGS * 15 / radarRefresh * (i + 1) * math.sin(avion.headingRad),
                                     AltitudeOne + VspeedOne * (i + 1) * 15 / radarRefresh))
            for avion2 in list(dictAvion.values()):
                if avion != avion2:
                    VspeedTwo = avion.evolution
                    AltitudeTwo = avion2.altitude
                    for i in range(12):
                        if math.sqrt((predictedPos[i][0] - (
                                avion2.x + avion2.speedGS * 15 / radarRefresh * (i + 1) * math.cos(
                                avion2.headingRad))) ** 2 +
                                     (predictedPos[i][1] - (
                                             avion2.y + avion2.speedGS * 15 / radarRefresh * (i + 1) * math.sin(
                                         avion2.headingRad))) ** 2) <= 5 / mapScale and abs(
                            predictedPos[i][2] - AltitudeTwo - VspeedTwo * (i + 1) * 15 / radarRefresh) < float(
                                1000) and abs(avion.altitude - avion2.altitude) <= 2500:
                            STCAtriggered = True
                            avion.STCA = True
                            avion2.STCA = True
            if not STCAtriggered:
                avion.STCA = False

    requests = []

sys.exit()
