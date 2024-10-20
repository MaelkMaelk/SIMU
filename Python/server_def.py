
# Native imports
import math

# Module imports
import xml.etree.ElementTree as ET

# Imports fichiers
import Python.geometry as geometry
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


def generateAvionXML(parentNode, avion, heureXML):

    """
    Transforme un avion packet en un element XML
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
