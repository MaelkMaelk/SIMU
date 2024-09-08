import math


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
