
# Native imports
import math
import copy

# Module imports
import xml.etree.ElementTree as ET

# Imports fichiers
import Python.geometry as geometry
from Python.paquets_avion import AvionPacket
from Python.valeurs_config import *


def STCA(avion1, avion2, carte) -> bool:
    """
    Calcule si on doit mettre le SCTA sur deux avions
    :param avion1: l'avion paquet
    :param avion2:
    :param carte: la carte de la map
    :return:
    """

    temps = geometry.distanceMinie((avion1.x, avion1.y), avion1.speedPx / radarRefresh, avion1.headingRad,
                                   (avion2.x, avion2.y), avion2.speedPx / radarRefresh, avion2.headingRad)

    if (math.sqrt(
        ((avion1.x + avion1.speedPx / radarRefresh * temps * math.cos(avion1.headingRad)) -
         (avion2.x + avion2.speedPx / radarRefresh * temps * math.cos(avion2.headingRad))) ** 2 +
        ((avion1.y + avion1.speedPx / radarRefresh * temps * math.sin(avion1.headingRad)) -
         (avion2.y + avion2.speedPx / radarRefresh * temps * math.sin(avion2.headingRad))) ** 2
    ) <= 5 / carte['mapScale']) and 0 < temps <= 120:  # si la distance est infèrieur à 5 nm

        if avion1.evolution == avion2.evolution == 0 and avion2.altitude == avion1.altitude:
            return True

        elif avion1.evolution == avion2.evolution == 0:
            return False

        elif abs(avion2.altitude - avion1.altitude) <= 1000:
            return True

        elif abs(avion2.altitude + avion2.evolution / radarRefresh * temps
                 - (avion1.altitude + avion1.evolution / radarRefresh * temps)) <= 3000:
            return True
    return False


def modifier_spawn_avion(avion_spawn_tuple: tuple, data: dict, carte: dict, perfos: dict):

    """
    Modifie les paramètres d'apparition d'un avion (refait un nouvel objet en entier avec l'init)
    :param perfos:
    :param carte:
    :param avion_spawn_tuple:
    :param data:
    :return:
    """

    avion_spawn = avion_spawn_tuple[1]

    a = avion_spawn_tuple[1]
    avion = AvionPacket(carte,
                        a.Id,
                        data['indicatif'],
                        data['avion'],
                        perfos[data['avion']],
                        a.route,
                        data['arrival'],
                        avion_spawn_tuple[0],
                        FL=data['FL'],
                        x=a.x,
                        y=a.y,
                        heading=a.heading,
                        PFL=data['PFL'],
                        medevac=a.medevac,
                        CPDLC=data['CPDLC'],
                        ExRVSM=data['ExRVSM'])

    return avion


def generateAvionXML(parentNode, avion, heureXML) -> None:

    """
    Transforme un avion packet en un element XML et l'inscrit dans un parent
    :param parentNode: La node XML dans laquelle on va inscrire notre nouvel avion
    :param avion: L'avion Packet qu'il faut transformer en XML
    :param heureXML:
    :return:
    """

    avionXML = ET.SubElement(parentNode, 'avion')
    avionXML.set('heure', str(heureXML))

    node = ET.SubElement(avionXML, 'indicatif')
    node.text = str(avion.indicatif)
    node = ET.SubElement(avionXML, 'aircraft')
    node.text = str(avion.aircraft)
    node = ET.SubElement(avionXML, 'route')
    node.text = str(avion.route['name'])
    node = ET.SubElement(avionXML, 'altitude')
    node.text = str(avion.altitude)
    node = ET.SubElement(avionXML, 'arrival')
    node.text = str(avion.arrival)

    node = ET.SubElement(avionXML, 'x')
    node.text = str(avion.x)
    node = ET.SubElement(avionXML, 'y')
    node.text = str(avion.y)

    node = ET.SubElement(avionXML, 'PFL')
    node.text = str(avion.PFL)

    node = ET.SubElement(avionXML, 'CPDLC')
    node.text = str(avion.CPDLC)

    node = ET.SubElement(avionXML, 'ExRVSM')
    node.text = str(avion.ExRVSM)


def compute_spawn_changes_impact(heure: float, avion_tuple: tuple, carte: dict):
    """
    Recalcule la position et les paramètres d'un avion depuis son spawn (ne prend pas en compte les clairances
     ultèrieures à celles au spawn)
    :param perfos: le dict des perfos de tous les avions
    :param carte: la carte du jeu
    :param heure: l'heure de la partie
    :param avion_tuple: le tuple de spawn de l'avion
    :return: retourne un objet paquet avion avec les paramètres recalculé en fonction du spawn et de l'heure
    """
    heure_diff = heure - avion_tuple[0]
    avion = copy.deepcopy(avion_tuple[1])

    for i in range(int(heure_diff // radarRefresh)):

        avion.move(carte)

    return avion


def prettyPrint(docXML):
    """
    Rend le XML joli à regarder
    :param docXML: le doc XML à transformer
    :return:
    """

    XMLstring = ''

    for line in docXML.toprettyxml().split('\n'):
        if not line.strip() == '':
            XMLstring += line + '\n'

    return XMLstring

