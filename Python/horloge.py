
def affichageHeure(heure: float) -> str:

    heures = str(round(heure // 3600 % 24))
    if len(heures) == 1:
        heures = '0' + heures
    minutes = str(round(heure % 3600 // 60))
    if len(minutes) == 1:
        minutes = '0' + minutes

    return heures + ':' + minutes


def heureXML(heure: float) -> str:

    """
    Renvoies un str avec l'heure en format hhmmss
    :param heure:
    :return:
    """

    heures = str(round(heure // 3600 % 24))
    if len(heures) == 1:
        heures = '0' + heures

    minutes = str(round(heure % 3600 // 60))
    if len(minutes) == 1:
        minutes = '0' + minutes

    secondes = str(round(heure % 3600 % 60))
    if len(secondes) == 1:
        secondes = '0' + secondes

    return heures + minutes + secondes


def heureFloat(heure: str) -> float:

    """
    Prends une heure str en format hhmm ou hhmmss et renvoie le nombre de secondes
    :param heure:
    :return:
    """
    if len(heure) == 6:
        return int(heure[0:2]) * 3600 + int(heure[2:4]) * 60 + int(heure[4:])

    return int(heure[0:2]) * 3600 + int(heure[2:]) * 60

