

# Imports fichiers


def check_is_zone_active(zone: dict, heure: float) -> bool:

    """
    Vérifie si une zone est active à une heure spécifique
    :param zone:
    :param heure:
    :return:
    """

    for creneau in zone['active']:

        if creneau[0] <= heure <= creneau[1]:
            return True

    return False
