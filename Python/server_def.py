
# Native imports
import math

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
    ) <= 5 / carte['mapScale']):  # si la distance est infèrieur à 5 nm

        if avion1.evolution == avion2.evolution == 0 and avion2.altitude == avion1.altitude:
            return True

        elif avion1.evolution == avion2.evolution == 0:
            return False

        elif abs(avion2.altitude + avion2.evolution / radarRefresh * temps
                 - (avion1.altitude + avion1.evolution / radarRefresh * temps)) <= 2000:
            return True

    return False


