import socket
from _thread import *
from queue import Queue
from network import MCAST_GRP, MCAST_PORT, port
from player import *
import pickle
import xml.etree.ElementTree as ET
import time
import struct


# On se connecte a internet pour avoir notre adresse IP locale... Oui oui
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(("8.8.8.8", 80))
servername = "mael"
server_ip = sock.getsockname()[0]
print(server_ip)
sock.close()
# fini on ferme le socket

# set up le socket pour le UDP, il répond au scan server coté client
pingSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
pingSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
pingSock.bind(('', MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
pingSock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# socket TCP pour les connections avec les clients
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((server_ip, port))
except socket.error as e:
    str(e)

s.listen(2)
print("Waiting for a connection, Server Started")


playerId = 0
dictAvion = {}
requests = []
gameMap = [{}, [], [], []]

# XML map loading


tree = ET.parse('XML/mapAPS.xml')
root = tree.getroot()
mapScale = float(root.find('scale').text)
print(mapScale)
size = float(root.find('size').text)
for point in root.find('points'):
    name = point.attrib['name']
    x = int(point.find('x').text)*size
    y = int(point.find('y').text)*size
    if point.find('balise') is not None:
        balise = bool(point.find('balise').text)
    else:
        balise = False
    if point.find('procedure') is not None:
        procedure = bool(point.find('procedure').text)
    else:
        procedure = False
    gameMap[0].update({name: (x, y, balise, procedure)})

for secteur in root.find('secteurs'):  # format map : [points, secteurs, segments, routes]
    contour = []
    for limite in secteur.findall('limite'):  # format secteurs : [[color, [point contours]]]
        x = int(limite.find('x').text)*size
        y = int(limite.find('y').text)*size
        contour.append((x, y))
    gameMap[1].append([[int(x) for x in secteur.attrib['color'].split(',')], contour])

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
        if ((x1, y1), (x2, y2)) not in gameMap[2] and x1 != x2 and y1 != y2:
            gameMap[2].append(((x1, y1), (x2, y2)))
        x1 = x2
        y1 = y2
    for next in route.findall('next'):
        listeNext.append(next.text)
    gameMap[3].append([nomRoute, routeType, listeRoutePoints, listeNext])
    # format route [nomRoute, routeType, listePoints, next]

aircraftType = {}
tree = ET.parse('XML/aircrafts.xml')
root = tree.getroot()

for aircraft in root:
    aircraftType.update({aircraft.attrib['name']:(int(aircraft.find('speed').text), int(aircraft.find('maxSpeed').text),
                                                  int(aircraft.find('ceiling').text), int(aircraft.find('ROC').text),
                                                  int(aircraft.find('ROD').text)) })

# format map : [points, secteurs, segments, routes]

game = Game()


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
            data = pickle.loads(conn.recv(2048*16))
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
                nombre+=1

    print("Lost connection")
    conn.close()


def threaded_waiting():
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
while True:
    inReq = reqQ.get()
    requests.append(inReq)
    for reqSublist in requests:
        for req in reqSublist:  # [Id avion, type requete, data]
            if req[1] == 'Add':
                req[2].Id = planeId
                dictAvion.update({planeId: req[2]})
                planeId += 1
            elif req[1] == 'Remove':
                dictAvion.pop(req[0])
            elif req[1] == 'Altitude':
                if req[2] <= dictAvion[req[0]].targetFL
                dictAvion[req[0]].targetFL = req[2]
            elif req[1] == 'Heading':
                dictAvion[req[0]].headingMode = True
                dictAvion[req[0]].intercept = True
                dictAvion[req[0]].targetHeading = req[2]
            elif req[1] == 'Warning':
                dictAvion[req[0]].Cwarning()
            elif req[1] == 'Part':
                dictAvion[req[0]].Cpart()
            elif req[1] == 'Direct':
                dictAvion[req[0]].headingMode = False
                dictAvion[req[0]].CnextPoint(req[2])
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

    if time.time() - temps >= radarRefresh and game.paused:
        temps = time.time()
        suppListe = []
        for avion in list(dictAvion.values()):
            supp = avion.move(gameMap) # si jamais l'avion doit etre supp, il le renvoie à la fin du move, sinon None
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
                predictedPos.append((avion.x + avion.speed * 15 / radarRefresh * (i+1) * math.cos(avion.headingRad),
                                        avion.y + avion.speed * 15 / radarRefresh * (i+1) * math.sin(avion.headingRad),
                                     AltitudeOne + VspeedOne * (i+1) * 15 / radarRefresh))
            for avion2 in list(dictAvion.values()):
                if avion != avion2:
                    VspeedTwo = avion.evolution
                    AltitudeTwo = avion2.altitude
                    for i in range(12):
                        if math.sqrt((predictedPos[i][0] - (avion2.x + avion2.speed * 15 / radarRefresh * (i+1) * math.cos(avion2.headingRad)))**2 +
                                     (predictedPos[i][1] - (avion2.y + avion2.speed * 15 / radarRefresh * (i+1) * math.sin(avion2.headingRad)))**2) <= 5 / mapScale and abs(predictedPos[i][2] - AltitudeTwo - VspeedTwo * (i+1) * 15 / radarRefresh) < float(1000) and abs(avion.altitude - avion2.altitude) <= 2500:
                            STCAtriggered = True
                            avion.STCA = True
                            avion2.STCA = True
            if not STCAtriggered:
                avion.STCA = False

    requests = []
