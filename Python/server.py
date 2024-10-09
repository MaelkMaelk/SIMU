
# Native imports
import socket
import sys
import pickle
from _thread import *
from queue import Queue
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import struct
import platform
from pathlib import Path

# Import fichiers
import Python.horloge as horloge
from Python.network import MCAST_GRP, MCAST_PORT, port
from Python.paquets_avion import *
import Python.server_def as server_def


dossierXML = Path("").absolute() / 'XML'

carte = 'carteSecteur.xml'
aircraftFile = 'aircraft.xml'
simu = 'simu.xml'
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
gameMap = {'points': {}, 'zones': {}, 'segments': [], 'routes': {}, 'mapScale': 0}

# XML map loading

tree = ET.parse(dossierXML / carte)
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

for zone in root.find('zones'):

    contour = []  # liste des points délimitant le contour du secteur, dans l'ordre de lecture xml
    nom = zone.attrib['name']
    active = False
    for limite in zone.findall('limite'):
        x = int(limite.find('x').text)
        y = int(limite.find('y').text)
        contour.append((x, y))

    if nom == 'SECTOR':
        active = True

    gameMap['zones'].update({nom: {
        'active': active,
        'couleur': [int(x) for x in zone.attrib['color'].split(',')],
        'contour': contour}})

dictSecteurs = {}
for secteur in root.find('secteurs'):

    nom = secteur.attrib['name']
    frequence = secteur.find('frequence').text
    etranger = False
    if secteur.find('etranger') is not None:
        if secteur.find('etranger').text == 'True':
            etranger = True

    dictSecteurs.update({nom: {'frequence': frequence, 'etranger': etranger}})

gameMap.update({'secteurs': dictSecteurs})

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
tree = ET.parse(dossierXML / aircraftFile)
root = tree.getroot()

for aircraft in root.find('aircrafts'):

    aircraftPerf = {}
    for XMLpoint in aircraft:
        try:
            XMLpointValue = float(XMLpoint.text)
        except:
            XMLpointValue = XMLpoint.text
        aircraftPerf.update({XMLpoint.tag: XMLpointValue})

    aircraftType.update(
        {aircraft.attrib['name']: aircraftPerf})

callsignList = {}
for callsign in root.find('callsigns'):
    callsignList.update({callsign.attrib['indicatif']: callsign.text})

gameMap.update({'callsigns': callsignList})
planeId = 0

simuTree = None
activiteZone = []
avionSpawnListe = []
try:
    simuTree = ET.parse(dossierXML / simu).getroot()

    heure = simuTree.find('heure').text
    heure = int(heure[0:2]) * 3600 + int(heure[2:4]) * 60 + int(heure[4:])

    game = Game(heure)

    avionsXML = simuTree.find('avions')
    for zone in simuTree.find('zones'):
        heureDebut = zone.find('debut').text
        heureDebut = int(heureDebut[0:2]) * 3600 + int(heureDebut[2:4]) * 60 + int(heureDebut[4:])
        heureFin = zone.find('fin').text
        heureFin = int(heureFin[0:2]) * 3600 + int(heureFin[2:4]) * 60 + int(heureFin[4:])
        activiteZone.append({
            'debut': heureDebut,
            'fin': heureFin,
            'nom': zone.find('nom').text
        })
    for avion in avionsXML:

        avionDict = {}

        for XMLpoint in avion:
            try:
                XMLpointValue = float(XMLpoint.text)
            except:
                XMLpointValue = XMLpoint.text
            avionDict.update({XMLpoint.tag: XMLpointValue})

        heureSpawn = avion.attrib['heure']
        heureSpawn = int(heureSpawn[0:2]) * 3600 + int(heureSpawn[2:4]) * 60 + int(heureSpawn[4:])

        for route in gameMap['routes']:
            if route == avionDict['route']:
                spawnRoute = gameMap['routes'][route]
                break
        if 'altitude' in avionDict:
            spawnFL = round(avionDict['altitude'] / 100)
        else:
            spawnFL = None
        avionPack = AvionPacket(
            gameMap,
            planeId,
            avionDict['indicatif'],
            avionDict['aircraft'],
            aircraftType[avionDict['aircraft']],
            spawnRoute,
            avionDict['arrival'] == 'True',
            FL=spawnFL,
            x=avionDict['x'],
            y=avionDict['y'])
        planeId += 1

        avionSpawnListe.append((heureSpawn, avionPack))
except:

    heure = input('Heure de début de simu, format: hhmm')
    heure = int(heure[0:2]) * 3600 + int(heure[2:]) * 60
    simuTree = ET.Element('simu')
    game = Game(heure)
    heureXML = ET.SubElement(simuTree, 'heure')
    heureXML.text = horloge.heureXML(game.heure)
    avionsXML = ET.SubElement(simuTree, 'avions')


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
                reply = Packet(packetId, game=game, dictAvions=dictAvion, carte=gameMap)

            conn.sendall(pickle.dumps(reply))
            nombre = 0

        except error:
            print(error)

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
accelerationTemporelle = 1
Running = True
while Running:
    inReq = reqQ.get()
    requests.append(inReq)
    for reqSublist in requests:
        for req in reqSublist:  # format requêtes : [Id avion, type requête, data]
            reqType = req[1]
            reqId = req[0]
            reqContent = None

            if len(req) == 3:
                reqContent = req[2]

            if reqType == 'Add':

                reqContent.Id = planeId
                dictAvion.update({planeId: reqContent})
                planeId += 1

                if mode_ecriture:
                    heure = horloge.heureXML(game.heure)
                    server_def.generateAvionXML(avionsXML, reqContent, heure)

            elif reqType == 'DelayedAdd':

                reqContent[1].Id = planeId
                avionSpawnListe.append((game.heure + reqContent[0], reqContent[1]))
                planeId += 1

                if mode_ecriture:
                    heure = horloge.heureXML(game.heure + reqContent[0])
                    server_def.generateAvionXML(avionsXML, reqContent[1], heure)

            elif reqType == 'Remove':
                dictAvion.pop(reqId)

            elif reqType == 'FL':
                dictAvion[reqId].selectedAlti = reqContent * 100

            elif reqType == 'PFL':
                dictAvion[reqId].PFL = reqContent
                dictAvion[reqId].changeXFL(gameMap)

            elif reqType == 'CFL':
                dictAvion[reqId].CFL = reqContent

            elif reqType == 'C_IAS':
                if reqContent:
                    dictAvion[reqId].clearedIAS = reqContent
                    dictAvion[reqId].clearedMach = None
                else:
                    dictAvion[reqId].clearedMach = None
                    dictAvion[reqId].clearedIAS = None

            elif reqType == 'C_Mach':
                if reqContent:
                    dictAvion[reqId].clearedMach = reqContent
                    dictAvion[reqId].clearedIAS = None
                else:
                    dictAvion[reqId].clearedMach = None
                    dictAvion[reqId].clearedIAS = None

            elif reqType == 'C_Rate':
                if reqContent:
                    dictAvion[reqId].clearedRate = reqContent
                else:
                    dictAvion[reqId].clearedRate = None

            elif reqType == 'Rate':
                if reqContent:
                    dictAvion[reqId].forcedEvo = True
                    signe = (dictAvion[reqId].evolution * reqContent) / abs(dictAvion[reqId].evolution * reqContent)
                    dictAvion[reqId].evolution = signe * reqContent
                else:
                    dictAvion[reqId].forcedEvo = False

            elif reqType == 'XFL':
                dictAvion[reqId].XFL = reqContent
                dictAvion[reqId].changeSortieSecteur(gameMap)

            elif reqType == 'XPT':
                dictAvion[reqId].XPT = reqContent

            elif reqType == 'C_HDG':
                dictAvion[reqId].clearedHeading = reqContent

            elif reqType == 'HDG':
                if type(reqContent) in [float, int]:
                    newHeading = reqContent
                elif reqContent[0] == '-':
                    newHeading = dictAvion[reqId].selectedHeading - int(reqContent[1:])
                elif reqContent[0] == '+':
                    newHeading = dictAvion[reqId].selectedHeading + int(reqContent[1:])
                dictAvion[reqId].headingMode = True
                dictAvion[reqId].selectedHeading = reqContent

            elif reqType == 'IAS':
                if reqContent:
                    dictAvion[reqId].forcedSpeed = True
                    dictAvion[reqId].selectedIAS = reqContent * 10
                else:
                    dictAvion[reqId].forcedSpeed = False

            elif reqType == 'Mach':
                if reqContent:
                    dictAvion[reqId].forcedSpeed = True
                    dictAvion[reqId].selectedMach = float(reqContent)
                else:
                    dictAvion[reqId].forcedSpeed = False

            elif reqType == 'DCT':
                dictAvion[reqId].clearedHeading = None
                dictAvion[reqId].DCT = reqContent

            elif reqType == 'Warning':
                dictAvion[reqId].warning = not dictAvion[reqId].warning

            elif reqType == 'Integre':
                dictAvion[reqId].integreOrganique = True

            elif reqType == 'Direct':
                dictAvion[reqId].headingMode = False
                for point in dictAvion[reqId].route['points']:
                    if point['name'] == reqContent:
                        dictAvion[reqId].nextPoint = point
                        break

            elif reqType == 'Route':
                dictAvion[reqId].nextRoute = reqContent
                dictAvion[reqId].changeRoute(gameMap)

            elif reqType == 'HighlightBouton':
                if reqContent in dictAvion[reqId].boutonsHighlight:  # si le bouton est déjà highlight alors:
                    dictAvion[reqId].boutonsHighlight.remove(reqContent)
                else:
                    dictAvion[reqId].boutonsHighlight.append(reqContent)

            elif reqType == 'Montrer':
                dictAvion[reqId].montrer = not dictAvion[reqId].montrer

            elif reqType == 'EtatFreq':
                dictAvion[reqId].updateEtatFreq(reqContent)

            elif reqType == 'FL?':
                dictAvion[reqId].FLInterro = not dictAvion[reqId].FLInterro

            elif reqType == 'Pause':
                game.paused = not game.paused

            elif reqType == 'Faster':
                accelerationTemporelle += 0.5

            elif reqType == 'Slower':
                if accelerationTemporelle > 0.5:
                    accelerationTemporelle -= 0.5

            elif reqType == 'Save' and mode_ecriture:
                xmlstr = server_def.prettyPrint(minidom.parseString(ET.tostring(simuTree)))
                with open("XML/simu.xml", "w") as f:
                    f.write(xmlstr)

    toBeRemovedFromSpawn = []
    for spawn in avionSpawnListe:
        if spawn[0] <= game.heure:
            toBeRemovedFromSpawn.append(spawn)
            dictAvion.update({spawn[1].Id: spawn[1]})

    for avion in toBeRemovedFromSpawn:
        avionSpawnListe.remove(avion)

    toBeRemovedFromActivite = []
    for activite in activiteZone:
        if activite['debut'] <= game.heure:
            gameMap['zones'][activite['nom']]['active'] = True
        if activite['fin'] <= game.heure:
            gameMap['zones'][activite['nom']]['active'] = False
            toBeRemovedFromActivite.append(activite)

    for activite in toBeRemovedFromActivite:
        activiteZone.remove(activite)

    if not game.paused:
        temps = time.time()  # si la game est sur pause alors on avance pas le temps
    elif time.time() - temps >= radarRefresh/accelerationTemporelle:
        game.heure += (time.time() - temps) * accelerationTemporelle
        temps = time.time()
        suppListe = []

        for avion in list(dictAvion.values()):
            # si jamais l'avion doit etre supp, il le renvoie à la fin du move, sinon None

            if avion.move(gameMap):
                suppListe.append(avion.Id)

        for avion in suppListe:
            dictAvion.pop(avion)

        for avion1 in dictAvion.values():
            STCAtriggered = False
            for avion2 in dictAvion.values():
                if avion1 != avion2:
                    STCAtriggered = server_def.STCA(avion1, avion2, gameMap)

                    if STCAtriggered:
                        avion1.STCA = True
                        avion2.STCA = True
            if not STCAtriggered:
                avion1.STCA = False

    requests = []

sys.exit()
