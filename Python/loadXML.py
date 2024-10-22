

# Native imports
import xml.etree.ElementTree as ET

# Import fichiers
from Python.paquets_avion import *


def loadSegmentsXML(listeXML) -> dict:

    """
    Parcours une balise XML qui liste les segments, retourne un dict avec les segments
    :param listeXML: la balise qui contient la liste des segments
    :return:
    """

    dictSeg = {}

    for segment in listeXML.find('segments'):
        condition = None
        nom = segment.find('nom').text
        points = []

        XPT = None
        EPT = None
        repli = None

        if segment.find('repli') is not None:
            repli = segment.find('repli').text

        if segment.find('condition') is not None:
            zone = segment.find('condition').find('zone').text
            actif = segment.find('condition').find('active').text == 'True'

            condition = (zone, actif)

        for point in segment.findall('point'):
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

            points.append(pointDict)

        dictSeg.update({nom: {'EPT': EPT,
                              'XPT': XPT,
                              'points': points,
                              'condition': condition,
                              'repli': repli,
                              'nom': nom}})

    return dictSeg


def loadAvionXML(avionXML, carte: dict, perfos: dict, heure: float, planeId: int) -> tuple[float, object]:

    """
    Prends une balise XML en entrée et retourne une liste d'avion à faire spawn
    :param planeId: l'Id de l'avion
    :param heure: l'heure de début de simu
    :param perfos: la liste des perfos avions
    :param carte: la carte du jeu
    :param avionXML: la balise XML qui contient les paramètres de l'avion
    :return: tuple (heure_de_spawn, avionPacket)
    """

    avionDict = {}

    for XMLpoint in avionXML:
        try:
            XMLpointValue = float(XMLpoint.text)
        except:
            XMLpointValue = XMLpoint.text
        avionDict.update({XMLpoint.tag: XMLpointValue})

    heureSpawn = avionXML.attrib['heure']
    heureSpawn = int(heureSpawn[0:2]) * 3600 + int(heureSpawn[2:4]) * 60 + int(heureSpawn[4:])

    for route in carte['routes']:
        if route == avionDict['route']:
            spawnRoute = carte['routes'][route]
            break

    if 'altitude' in avionDict:
        spawnFL = round(avionDict['altitude'] / 100)
    else:
        spawnFL = None

    if 'CPDLC' in avionDict:
        CPDLC = avionDict['CPDLC'] == 'True'
    else:
        CPDLC = False

    if 'ExRVSM' in avionDict:
        ExRVSM = avionDict['ExRVSM'] == 'True'
    else:
        ExRVSM = False

    avionPack = AvionPacket(
        carte,
        planeId,
        avionDict['indicatif'],
        avionDict['aircraft'],
        perfos[avionDict['aircraft']],
        spawnRoute,
        avionDict['arrival'] == 'True',
        heureSpawn,
        FL=spawnFL,
        CPDLC=CPDLC,
        ExRVSM=ExRVSM,
        x=avionDict['x'],
        y=avionDict['y'])

    # modifications de l'avion après spawn : ex vérrouillage vitesse

    if 'clearedSpeed' in avionDict:  # format : k230 ou M0.82 par exemple
        avionPack.forcedSpeed = True  # on met la vitesse forcée en vraie !!

        if avionDict['clearedSpeed'][-1] in ['-', '+']:  # s'il y a un symbole à la fin, on l'enlève
            vitesseTxt = avionDict['clearedSpeed'][1:-1]
        else:
            vitesseTxt = avionDict['clearedSpeed'][1:]  # on enlève la lettre au début

        if avionDict['clearedSpeed'][0] in ['m', 'M']:  # ici, on est donc en point de mach
            vitesse = float(vitesseTxt)
            avionPack.clearedMach = avionDict['clearedSpeed'][1:]
            avionPack.mach = vitesse
            avionPack.selectedMach = vitesse

        else:  # et ici en vitesse indiquée IAS
            vitesse = int(vitesseTxt)
            avionPack.clearedIAS = avionDict['clearedSpeed'][1:]
            avionPack.speedIAS = vitesse
            avionPack.selectedIAS = vitesse

    return heureSpawn, avionPack

