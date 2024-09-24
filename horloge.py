
def affichageHeure(heure: float) -> str:

    heures = str(round(heure // 3600 % 24))
    if len(heures) == 1:
        heures = '0' + heures
    minutes = str(round(heure % 3600 // 60))
    if len(minutes) == 1:
        minutes = '0' + minutes

    return heures + ':' + minutes
