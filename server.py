import socket
from _thread import *
from player import *
import pickle
import xml.etree.ElementTree as ET

server = "10.1.102.173"
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
print("Waiting for a connection, Server Started")


players = []
requests = []
gameMap = [{}, [], [], []]
# XML map loading

tree = ET.parse('XML/map.xml')
root = tree.getroot()
scale = float(root.find('scale').text)
size = float(root.find('size').text)
for point in root.find('points'):
    name = point.attrib['name']
    x = int(point.find('x').text)*size
    y = int(point.find('y').text)*size
    balise = bool(point.find('balise').text)
    gameMap[0].update({name: (x, y, balise)})

for limite in root.find('secteur'):
    x = int(limite.find('x').text)*size
    y = int(limite.find('y').text)*size
    gameMap[1].append((x, y))

for route in root.find('routes'): #construction des routes
    routeAdd = []
    routeAdd.append(gameMap[0][route.find('spawn').text])
    routeAdd.append(route.find('last').text)
    routeAdd.append({})

    sorties = []
    for sortie in route.findall('sortie'):
        sorties.append((sortie.text, int(sortie.attrib['min']), int(sortie.attrib['max'])))
    routeAdd.append(sorties)

    x1 = gameMap[0][route.find('spawn').text][0]
    y1 = gameMap[0][route.find('spawn').text][1]
    for point in route.findall('point'):
        routeAdd[2].update({point.text: gameMap[0][point.text]})
        y2 = gameMap[0][point.text][1]
        x2 = gameMap[0][point.text][0]
        if ((x1, y1), (x2, y2)) not in gameMap[2] and x1 != x2 and y1 != y2:
            gameMap[2].append(((x1, y1), (x2, y2)))
        x1 = x2
        y1 = y2
    gameMap[3].append(routeAdd)
    # format route : [spawn, last, {points:()}, secteurSortie]


aircraftType = {}
tree = ET.parse('XML/aircrafts.xml')
root = tree.getroot()

for aircraft in root:
    aircraftType.update({aircraft.attrib['name']:(int(aircraft.find('speed').text), int(aircraft.find('maxSpeed').text),
                                                  int(aircraft.find('ceiling').text), int(aircraft.find('ROC').text),
                                                  int(aircraft.find('ROD').text)) })
game = Game(0)
# format map : [points, secteur, segments, routes]

def threaded_client(conn, caca):
    global players
    global requests
    global map
    global aircraftType
    players.append(Player(game.playerNb, False))
    requests.append([])
    game.connection()
    packet = Packet(game, players, requests, gameMap, aircraftType)
    conn.send(pickle.dumps(packet))
    reply = ""
    while True:
        try:
            data = pickle.loads(conn.recv(2048*16))
            playerId = data.getPlayers().getId()
            players[playerId] = data.getPlayers()
            requests[playerId] = data.getRequests()

            if not data:
                print("Disconnected")
                break
            else:
                reply = Packet(game, players, requests)
                '''
                print("Received: ", data)
                print("Sending : ", reply)
                '''
            conn.sendall(pickle.dumps(reply))
        except:
            break

    print("Lost connection")
    players[playerId].listeAvions=[]
    conn.close()


while True:
    conn, addr = s.accept()
    print("Connected to:", addr)
    start_new_thread(threaded_client, (conn , 0))
