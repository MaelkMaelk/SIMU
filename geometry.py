import math
import numpy as np


def calculateHeading(x: int, y: int, xPoint: int, yPoint: int):
    if y > yPoint:
        if x > xPoint:
            heading = (math.atan(abs(y - yPoint) / (abs(x - xPoint)))) * 180 / math.pi
            heading += 270
        else:
            heading = (math.atan(abs(x - xPoint) / (abs(y - yPoint)))) * 180 / math.pi
    elif x > xPoint:
        heading = (math.atan(abs(x - xPoint) / (abs(y - yPoint)))) * 180 / math.pi
        heading += 180
    else:
        heading = (math.atan(abs(y - yPoint) / (abs(x - xPoint)))) * 180 / math.pi
        heading += 90

    heading = heading % 360
    return heading


def calculateDistance(x1: int, y1: int, x2: int, y2: int):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def calculateShortestPoint(pointDroite1: list[float, float], pointDroite2: list[float, float],
                           point: list[float, float]):
    """
    Calcule le point sur une droite où la distance ets la plus courte à un point
    :param pointDroite1: 1er point pour définir la droite, vecteur2 (x, y)
    :param pointDroite2: 2em point pour définir la droite, vecteur2 (x, y)
    :param point: point avec lequel on fait le calcul, vecteur2 (x, y)
    :return: retourne le point d'intersection du segment et de la droite (x, y)
    """

    if not pointDroite1[0] == pointDroite2[0]:  # si la droite est pile verticale, alors les calculs ne fonctionnent pas
        # on calcule le coeff directeur de la droite
        coeffdroite1 = (pointDroite1[1] - pointDroite2[1]) / (pointDroite1[0] - pointDroite2[0])
        # on calcule l'ordonnée à l'origine
        ordonnee1 = pointDroite1[1] - coeffdroite1 * pointDroite1[0]
        # on prend l'opposée de l'inverse de ce coeff, qui correspond celui de la droite perpendiculaire
        coeffdroitePerp = - 1 / coeffdroite1
        # on calcule l'ordonnée à l'origine à partir du point
        ordonnee2 = point[1] - coeffdroitePerp * point[0]

        left_side = np.array([[-coeffdroite1, 1], [-coeffdroitePerp, 1]])
        right_side = np.array([ordonnee1, ordonnee2])
    else:  # si la droite est verticale alors c'est super simple de trouver les coords du point
        return pointDroite1[0], point[1]

    # solve for x and y
    return np.linalg.inv(left_side).dot(right_side)


def calculateIntersection(point1Droite, point2Droite, point1Droite2, point2Droite2) -> tuple[float, float]:

    """
    Calcule l'intersection entre deux droites
    :param point1Droite:  1er point pour définir la droite, vecteur2 (x, y)
    :param point2Droite: 2em point pour définir la droite, vecteur2 (x, y)
    :param point1Droite2: 1er point pour définir la droite 2, vecteur2 (x, y)
    :param point2Droite2: 2em point pour définir la droite 2, vecteur2 (x, y)
    :return: Le point d'intersection des deux droites (x, y)
    """
    point = (0, 0)
    coeffdroite1 = 0
    coeffdroite2 = 0
    ordonnee1 = 0
    ordonnee2 = 0

    if not point1Droite[0] == point2Droite[0]:  # si la droite est pile verticale, alors les calculs ne fonctionnent pas
        # on calcule le coeff directeur de la droite
        coeffdroite1 = (point1Droite[1] - point2Droite[1]) / (point1Droite[0] - point2Droite[0])
        # on calcule l'ordonnée à l'origine
        ordonnee1 = point1Droite[1] - coeffdroite1 * point1Droite[0]
    else:  #
        point = (point1Droite[0], 0)

    if not point1Droite2[0] == point2Droite2[0]:
        # on calcule le coeff directeur de la droite
        coeffdroite2 = (point1Droite2[1] - point2Droite2[1]) / (point1Droite2[0] - point2Droite2[0])
        # on calcule l'ordonnée à l'origine
        ordonnee2 = point1Droite2[1] - coeffdroite2 * point1Droite2[0]
    elif point != (0, 0):  # ici les deux droites sont verticales
        print("Pas d'intersection entre ces deux droites, elles sont verticales toute les deux")
    else:
        point = (point1Droite2[0], 0)

    if point == (0, 0):  # si aucune droite n'est verticale, on résout le système

        left_side = np.array([[-coeffdroite1, 1], [-coeffdroite2, 1]])
        right_side = np.array([ordonnee1, ordonnee2])
        point = np.linalg.inv(left_side).dot(right_side)

    elif point == (point1Droite[0], 0):  # si la 1ere droite est verticale :
        point = (point1Droite[0], point1Droite[0] * coeffdroite2 + ordonnee2)

    else:  # si la 2eme droite est verticale
        point = (point1Droite2[0], point1Droite2[0] * coeffdroite1 + ordonnee1)

    return point


def calculateAngle(principal, secondaire):
    """Calcul des angles entre deux droites orientées.
    L'angle retourné en 1er est celui en aval de la droite principale et en amont de la secondaire
    :arg principal: droite, soit 2 points (x1,y1,x2,y2) dans le sens orienté, soit un radial
    :arg secondaire: droite, soit 2 points (x1,y1,x2,y2) dans le sens orienté, soit un radial
    :returns [angle d'interception, l'autre angle]"""

    # on calcule dabord les radials
    if type(principal) in [list, tuple]:
        principal = calculateHeading(principal[0], principal[1], principal[2], principal[3])
    if type(secondaire) in [list, tuple]:
        secondaire = calculateHeading(secondaire[0], secondaire[1], secondaire[2], secondaire[3])

    # on fait ensuite les soustractions pour obtenir les angles
    if principal <= secondaire and secondaire - principal <= 180:
        return [secondaire - principal, 180 - secondaire + principal]
    elif principal <= secondaire:
        return [principal - secondaire + 360, secondaire - 180 - principal]
    elif principal - secondaire <= 180:
        return [principal - secondaire, 180 - principal + secondaire]
    else:
        return [secondaire - principal + 360, principal - 180 - secondaire]
