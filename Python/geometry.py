
# Native imports
import math

# Module imports
import numpy as np
from scipy.optimize import minimize


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


def calculateDistance(x1: int | float, y1: int | float, x2: int | float, y2: int | float):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def calculateShortestPoint(pointDroite1: list[float, float] | tuple[float, float],
                           pointDroite2: list[float, float] | tuple[float, float],
                           point: list[float, float] | tuple[float, float],
                           segment=False
                           ):
    """
    Calcule le point sur une droite où la distance ets la plus courte à un point
    :param pointDroite1: 1er point pour définir la droite, vecteur2 (x, y)
    :param pointDroite2: 2em point pour définir la droite, vecteur2 (x, y)
    :param point: point avec lequel on fait le calcul, vecteur2 (x, y)
    :param segment: si on doit considérer comme un objet ou comme une droite
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

        solution = pointDroite1[0], point[1]

        if segment:

            if not pointDroite1[1] <= pointDroite2[1]:  # on trie les points pour que le 1 ai le y le plus petit
                pointDroite1, pointDroite2 = pointDroite2, pointDroite1

            if point[1] <= pointDroite1[1]:  # on vérifie ensuite si le y est ou non compris dans le segment
                solution = pointDroite1

            elif point[1] >= pointDroite2[1]:
                solution = pointDroite2

        return solution

    # solve for x and y
    solution = np.linalg.inv(left_side).dot(right_side)

    if segment:
        if not pointDroite1[0] <= pointDroite2[0]:  # on trie les points pour que le 1 ai le x le plus petit
            pointDroite1, pointDroite2 = pointDroite2, pointDroite1

        if solution[0] <= pointDroite1[0]:  # on vérifie ensuite si le x est ou non compris dans le segment
            solution = pointDroite1

        elif solution[0] >= pointDroite2[0]:
            solution = pointDroite2

    return solution


def calculateIntersection(point1Droite, point2Droite,
                          point1Droite2, point2Droite2) -> tuple[float, float]:

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


def distanceMinie(pos1: tuple[float, float], vitesse1: float, heading1: float,
                  pos2: tuple[float, float], vitesse2: float, heading2: float) -> float:
    """
    Calcule la position future de deux avions où la distance sera minimale entre les deux.
    :param pos1: Position actuelle de l'avion 1 en px
    :param vitesse1: Vitesse actuelle de l'avion 1 en px/sec
    :param heading1: Heading actuelle de l'avion 1 en radiants
    :param pos2: Position actuelle de l'avion 2 en px
    :param vitesse2: Vitesse actuelle de l'avion 2 en px/sec
    :param heading2: Heading actuelle de l'avion 2 en radiants
    :return: Temps dans lequel la distance sera la plus faible
    """

    x0 = 1.0

    caca = minimize(
        distanceMiniEnFduTemps, x0, args=(pos1, vitesse1, heading1, pos2, vitesse2, heading2),
        method='Nelder-Mead', tol=1e-4
    )
    return caca.x[0]


def distanceMiniEnFduTemps(temps, pos1: tuple[float, float], vitesse1: float, heading1: float,
                           pos2: tuple[float, float], vitesse2: float, heading2: float):

    return math.sqrt(
        ((pos1[0] + vitesse1 * temps * math.cos(heading1)) - (pos2[0] + vitesse2 * temps * math.cos(heading2))) ** 2 +
        ((pos1[1] + vitesse1 * temps * math.sin(heading1)) - (pos2[1] + vitesse2 * temps * math.sin(heading2))) ** 2
    )


def findClosestSegment(route: list, position: tuple[float, float], points: dict) -> tuple:
    """
    Retourne les 2 points du segment de la route le plus proche de notre position dans l'ordre de la route.
    :param route: La route qu'on analyse
    :param position: La position qu'on veut comparer
    :param points: La carte du jeu
    :return:
    """

    start = route[0]
    end = route[0]
    distance = 99999999

    for index in range(len(route) - 1):  # dans cette boucle, on cherche à quel segment on est le plus proche
        point = route[index]
        point2 = route[index + 1]
        coords1 = (points[point['name']][0], points[point['name']][1])
        coords2 = (points[point2['name']][0], points[point2['name']][1])

        # d'abord, on trouve le point le plus proche de notre pos sur ce segment
        intersection = calculateShortestPoint(
            coords1, coords2, position, True)

        disancte = calculateDistance(position[0], position[1], intersection[0], intersection[1])

        if disancte <= distance:
            start = point
            end = point2
            distance = disancte

    return start, end
