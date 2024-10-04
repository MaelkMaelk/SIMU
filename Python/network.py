
# Native imports
import socket
import pickle

port = 5555
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007


class Network:

    global port
    def __init__(self, server_ip):

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip
        self.port = port
        self.addr = (self.server, self.port)
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            self.client.connect(self.addr)
            return pickle.loads(self.client.recv(2048 * 16))
        except:
            pass

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            return pickle.loads(self.client.recv(2048 * 16))
        except socket.error as e:
            print(e)
