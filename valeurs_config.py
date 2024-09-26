radarRefresh = 4  # temps en s pour le refresh radar
heureEnRefresh = radarRefresh / 3600  # pour calculer la vitesse des avions (conversion par heure en par refresh)
nmToFeet = 6076
secteurDefault = 'RU'  # secteur par défault, si le programme n'arrive pas à trouver un secteur de sortie
altiDefault = 30000  # alti en pied par défault, si on ne rentre pas d'alti pour spawn un avion
acceldefault = 3  # accélération/decelération de kt par refresh
turnRateDefault = 10  # turnrate/refresh par défault
liste_etat_freq = ['previousFreq', 'previousShoot', 'inFreq', 'nextCoord', 'nextShoot', 'nextFreq']
secteurBoundaries = [245, 365]
plotSize = 5  # taille des plots avions
listeEtrangers = ['G2', 'M2']  # liste des secteurs ajdacents non interopérables
dragDelay = 250  # on utilise cette valeur seuil pour déterminer si on doit cliquer sur un bouton ou drag l'etiquette
offsettEtiquetteDefault = 30
