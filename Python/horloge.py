
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
