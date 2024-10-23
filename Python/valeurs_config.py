radarRefresh = 4  # temps en s pour le refresh radar
heureEnRefresh = radarRefresh / 3600  # pour calculer la vitesse des avions (conversion par heure en par refresh)
nmToFeet = 6076
secteurDefault = 'RU'  # secteur par défault, si le programme n'arrive pas à trouver un secteur de sortie
altiDefault = 30000  # alti en pied par défault, si on ne rentre pas d'alti pour spawn un avion
acceldefault = 3  # accélération/decelération en kt par refresh
acceldefaultMach = 0.003  # accélération/decelération en point de mach par refresh
turnRateDefault = 10  # turnrate/refresh par défault
liste_etat_freq = ['previousFreq', 'previousShoot', 'inFreq', 'nextCoord', 'nextShoot', 'nextFreq']
valeurCoord = 8  # combien de minute avant la sortie la coord passe
plotSize = 5  # taille des plots avions
dragDelay = 300  # on utilise cette valeur seuil pour déterminer si on doit cliquer sur un bouton ou drag l'etiquette
offsettEtiquetteDefault = 30  # de combien les etiquettes sont décalées en px à quand on les dessine la 1ere fois
temps_disparition_menus = 300  # en combien de milli sec les menus disparaissent après ne plus être survolé
temps_affichage_text = 1000  # combien de milli sec les text s'affiche sur l'écran, par ex "sauvegardé"
altitude_conversion = 27500
altitude_cruise = 25000

delaiScreen = 6900
replayMode = False
