import socket

from network import MCAST_GRP, MCAST_PORT

def serverBrowser():
    """Lan scan et server browser en une fonction
    renvoie une adresse IP en str"""

    serverList = {}
    MULTICAST_TTL = 2

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
    sock.settimeout(0.4)

    sock.sendto(b"Server?", (MCAST_GRP, MCAST_PORT))

    while True:
        try:
            data, address = sock.recvfrom(10240)
        except socket.timeout:
            break
        serverList.update({data: address})
    sock.close()
    if len(serverList) <= 1:
        return list(serverList.values())[0][0]
    print('Liste des serveurs actifs:')
    for i in range(len(list(serverList.keys()))):
        print(i, ' - ', list(serverList.keys())[i], '\n')
    return list(serverList.values())[int(input('Quel serveur voulez vous rejoindre ? Entrez le numéro'))][0]