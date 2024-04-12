import socket
import sys
from _thread import *
from queue import Queue
from network import MCAST_GRP, MCAST_PORT, port
from player import *
import pickle
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import struct
import platform

SIMU = 'simu.xml'
mode_ecriture = True

# On se connecte a internet pour avoir notre adresse IP locale... Oui oui
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(("8.8.8.8", 80))
servername = input('Nom du serveur:')
server_ip = sock.getsockname()[0]
sock.close()
# fini on ferme le socket

print(servername, server_ip)

if platform.system() == 'Windows': #on vérifie pour faire marcher le Mcast sur windows
    mcast_group = ''
else:
    mcast_group = MCAST_GRP  # on prend celui de network si on est sur linux

# set up le socket pour le UDP, il répond au scan server coté client
pingSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
pingSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
pingSock.bind((mcast_group, MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
pingSock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# socket TCP pour les connections avec les clients
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((server_ip, port))
except socket.error as e:
    str(e)

s.listen(2)

playerId = 0
dictAvion = {}
requests = []
segments = {}
gameMap = [{}, [], segments, []]

# XML map loading

tree = ET.parse('XML/mapAPS.xml')
root = tree.getroot()
mapScale = float(root.find('scale').text)
size = float(root.find('size').text)

for point in root.find('points'):
    name = point.attrib['name']
    x = int(point.find('x').text) * size
    y = int(point.find('y').text) * size
    if point.find('balise') is not None:
        balise = bool(point.find('balise').text)
    else:
        balise = False
    if point.find('procedure') is not None:
        procedure = bool(point.find('procedure').text)
    else:
        procedure = False
    gameMap[0].update({name: (x, y, balise, procedure)})

for secteur in root.find('secteurs'):
    contour = []
    for limite in secteur.findall('limite'):  # format secteurs : [[color, [point contours]]]
        x = int(limite.find('x').text) * size
        y = int(limite.find('y').text) * size
        contour.append((x, y))
    gameMap[1].append([[int(x) for x in secteur.attrib['color'].split(',')], contour])

# parsing des routes pour conaître tout les types de routes, pour l'affichage des segments

for route in root.find('routes'):
    if route.find('Type').text not in segments:
        segments.update({route.find('Type').text: []})

gameMap[2] = segments

for route in root.find('routes'):  # construction des routes
    nomRoute = route.attrib['name']
    routeType = route.find('Type').text
    listeNext = []
    listeRoutePoints = []

    x1 = gameMap[0][route.find('point').find('name').text][0]
    y1 = gameMap[0][route.find('point').find('name').text][1]

    for point in route.findall('point'):
        pointDict = {}
        pointDict.update({'name': point.find('name').text})
        for XMLpoint in point:
            try:
                XMLpointValue = int(XMLpoint.text)
            except:
                XMLpointValue = XMLpoint.text
            pointDict.update({XMLpoint.tag: XMLpointValue})
        listeRoutePoints.append(pointDict)

        y2 = gameMap[0][point.find('name').text][1]
        x2 = gameMap[0][point.find('name').text][0]
        if ((x1, y1), (x2, y2)) not in gameMap[2][routeType] and x1 != x2 and y1 != y2:
            gameMap[2][routeType].append(((x1, y1), (x2, y2)))
        x1 = x2
        y1 = y2
    for next in route.findall('next'):
        listeNext.append(next.text)
    gameMap[3].append([nomRoute, routeType, listeRoutePoints, listeNext])
    # format route [nomRoute, routeType, listePoints, next]

gameMap.append(mapScale)
axes = []

# format axes = (nom, point, radial, finale, chevron, dsiplaySize)
for axe in root.find('axes'):
    try:
        chevron = int(axe.find('chevron').text)
    except:
        chevron = axe.find('chevron').text

    axes.append((axe.attrib['name'], axe.find('point').text, int(axe.find('radial').text), axe.find('next').text, chevron, int(axe.find('displaySize').text)))

zoneListe = []

for zone in root.find('zones'):
    zoneDict = {}
    zoneDict.update({'name': zone.attrib['name']})

    for XMLpoint in zone:
        try:
            XMLpointValue = int(XMLpoint.text)
        except:
            XMLpointValue = XMLpoint.text
        zoneDict.update({XMLpoint.tag: XMLpointValue})
    zoneListe.append(zoneDict)


gameMap.append(axes)
gameMap.append(zoneListe)

aircraftType = {}
tree = ET.parse('XML/aircrafts.xml')
root = tree.getroot()

for aircraft in root:
    aircraftType.update(
        {aircraft.attrib['name']: (int(aircraft.find('speed').text), int(aircraft.find('maxSpeed').text),
                                   int(aircraft.find('ceiling').text), int(aircraft.find('ROC').text),
                                   int(aircraft.find('ROD').text))})

# format map : [points, secteurs, segments, routes, mapScale, axes, zones]

try:
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
except:

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
    packet = Packet(packetId, game=game, dictAvions=dictAvion, map=gameMap, perfos=aircraftType)
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
        for req in reqSublist:  # [Id avion, type requete, data]
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

                    generateAvionXML(avionsXML, heures + minutes, req[2].indicatif, req[2].aircraft, req[2].routeFull[0], req[2].altitude, xEcriture=req[2].x, yEcriture=req[2].y, PFLEcriture=req[2].PFL)

            elif req[1] == 'Remove':
                dictAvion.pop(req[0])
            elif req[1] == 'Altitude':
                if req[2] <= dictAvion[req[0]].altitude:
                    dictAvion[req[0]].evolution = - dictAvion[req[0]].maxROD
                else:
                    dictAvion[req[0]].evolution = dictAvion[req[0]].maxROC
                dictAvion[req[0]].targetFL = req[2]
                dictAvion[req[0]].forcedEvo = True
            elif req[1] == 'Intercept':
                dictAvion[req[0]].intercept = True
                dictAvion[req[0]].changeAxe(req[2], gameMap)
            elif req[1] == 'Heading':
                dictAvion[req[0]].headingMode = True
                dictAvion[req[0]].targetHeading = req[2]
            elif req[1] == 'IAS':
                dictAvion[req[0]].targetIAS = req[2]
            elif req[1] == 'Warning':
                dictAvion[req[0]].Cwarning()
            elif req[1] == 'Part':
                dictAvion[req[0]].Cpart()
            elif req[1] == 'Direct':
                dictAvion[req[0]].headingMode = False
                dictAvion[req[0]].CnextPoint(req[2])
            elif req[1] == 'Route':
                dictAvion[req[0]].nextRoute = req[2]
                dictAvion[req[0]].changeRoute(gameMap)
            elif req[1] == 'PFL':
                dictAvion[req[0]].PFL = req[2]
            elif req[1] == 'Mouvement':
                dictAvion[req[0]].Cmouvement()
            elif req[1] == 'Montrer':
                dictAvion[req[0]].montrer = not dictAvion[req[0]].montrer
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
                with open("simu.xml", "w") as f:
                    f.write(xmlstr)

    toBeRemovedFromSpawn = []
    for spawn in avionSpawnListe:
        if spawn[0] <= game.heure:
            for route in gameMap[3]:
                if route[0] == spawn[1]['route']:
                    spawnRoute = route
                    break
            if 'altitude' in spawn[1]:
                spawnFL = round(spawn[1]['altitude']/100)
            else:
                spawnFL = None
            dictAvion.update({planeId: AvionPacket(gameMap, planeId, spawn[1]['indicatif'], spawn[1]['aircraft'], aircraftType[spawn[1]['aircraft']], spawnRoute, FL=spawnFL)})
            toBeRemovedFromSpawn.append(spawn)
            planeId += 1

    for avion in toBeRemovedFromSpawn:
        avionSpawnListe.remove(avion)

    if time.time() - temps >= radarRefresh/accelerationTemporelle and game.paused:
        game.heure += (time.time() - temps) * accelerationTemporelle
        temps = time.time()
        suppListe = []
        for avion in list(dictAvion.values()):
            supp = avion.move(gameMap)  # si jamais l'avion doit etre supp, il le renvoie à la fin du move, sinon None
            if supp is not None:
                suppListe.append(avion.Id)
        for avion in suppListe:
            dictAvion.pop(avion)
        for avion in list(dictAvion.values()):
            # tout les calculs de distances sont ici effectués en pixel, la conversion se fait avec le mapScale
            STCAtriggered = False
            predictedPos = []
            VspeedOne = avion.evolution
            AltitudeOne = avion.altitude
            for i in range(12):
                predictedPos.append((avion.x + avion.speed * 15 / radarRefresh * (i + 1) * math.cos(avion.headingRad),
                                     avion.y + avion.speed * 15 / radarRefresh * (i + 1) * math.sin(avion.headingRad),
                                     AltitudeOne + VspeedOne * (i + 1) * 15 / radarRefresh))
            for avion2 in list(dictAvion.values()):
                if avion != avion2:
                    VspeedTwo = avion.evolution
                    AltitudeTwo = avion2.altitude
                    for i in range(12):
                        if math.sqrt((predictedPos[i][0] - (
                                avion2.x + avion2.speed * 15 / radarRefresh * (i + 1) * math.cos(
                                avion2.headingRad))) ** 2 +
                                     (predictedPos[i][1] - (
                                             avion2.y + avion2.speed * 15 / radarRefresh * (i + 1) * math.sin(
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