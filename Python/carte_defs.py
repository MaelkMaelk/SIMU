

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


def check_is_segment_active(segment: dict, heure: float, zones: dict) -> bool:

    """
    Vérifie si un segment est actif ou non
    :param zones: le dict des zones de la carte
    :param segment:
    :param heure:
    :return:
    """

    if 'condition' not in segment:  # si c'est un segment sans condition, il est actif
        return True

    zone = zones[segment['condition'][0]]
    if check_is_zone_active(zone, heure) == segment['condition'][1]:
        # si la condition est valide, il est actif
        return True

    return False
