import math
import numpy as np


def calculateHeading(x, y, xPoint, yPoint):
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


def calculateDistance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def calculateShortestPoint(pointDroite1, pointDroite2, point):
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
