
# Import Modules

import pygame
import pygame_gui

# Import fichiers
import horloge as horloge


class flightDataWindow:

    def __init__(self):

        width = 400
        height = 150

        self.window = pygame_gui.elements.UIWindow(
            pygame.Rect((20, 20), (width, height)),
            window_display_title="Flight Data Window",
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc')
        )

        self.ligneUn = pygame_gui.elements.UILabel(
            pygame.Rect((0, 5), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
        )

        self.ligneDeux = pygame_gui.elements.UILabel(
            pygame.Rect((0, 0), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
            anchors={'top': 'top', 'top_target': self.ligneUn}
        )

        self.ligneTrois = pygame_gui.elements.UIButton(
            pygame.Rect((0, 2), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
            anchors={'top': 'top', 'top_target': self.ligneDeux}
        )

        self.ligneQuatre = pygame_gui.elements.UILabel(
            pygame.Rect((0, 2), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
            anchors={'top': 'top', 'top_target': self.ligneTrois}
        )

        self.ligneCinq = pygame_gui.elements.UILabel(
            pygame.Rect((0, 0), (width, -1)),
            container=self.window,
            text='',
            object_id=pygame_gui.core.ObjectID('@flightDataWindow', 'blanc'),
            anchors={'top': 'top', 'top_target': self.ligneQuatre}
        )

    def linkAvion(self, avion, points: list, heure) -> None:
        """
        Associe la FDW à un avion
        :param avion: L'avion auquel on doit s'associer
        :param points: La liste des points de la carte
        :param heure: L'heure courante, pour pouvoir calculer les estimées
        :return:
        """
        ETX = avion.papa.calculeEstimate(points, avion.papa.XPT)  # heure de sortie
        ETE = avion.papa.calculeEstimate(points, avion.papa.DCT)  # heure d'entrée

        ETE = horloge.affichageHeure(ETE + heure)
        ETX = horloge.affichageHeure(ETX + heure)

        if avion.papa.ExRVSM:
            RVSMtext = 'ExW'
        else:
            RVSMtext = 'OkW'

        couleur = avion.etiquette.indicatif.get_class_ids()[1]
        objectID = pygame_gui.core.ObjectID('@flightDataWindow', couleur)

        for label in [self.ligneUn, self.ligneDeux, self.ligneTrois, self.ligneQuatre, self.ligneCinq]:
            label.change_object_id(objectID)

        text = (str(avion.papa.indicatif) + '       ' + str(avion.papa.aircraft)
                + '          ' + avion.papa.modeA + '       | N' + str(round(avion.papa.speedIAS)) + ' Ok8  OkR  ' + RVSMtext)
        self.ligneUn.set_text(text)

        text = avion.papa.callsignFreq + '                                           ' + avion.papa.medevac
        self.ligneDeux.set_text(text)

        text = (avion.papa.provenance + '   ' + avion.papa.destination + '  R' + str(avion.papa.PFL)
                + ' ' + str(round(avion.papa.altitude / 100)) + ' ' + str(avion.papa.PFL)
                + '    ' + avion.papa.EPT + '      ' + avion.papa.XPT + '  X' + str(avion.papa.XFL))
        self.ligneTrois.set_text(text)

        text = ('C' + str(avion.papa.CFL) + '   ' + str(avion.papa.DCT) + '        S' + '      R                   |'
                + ETE + '          ' + ETX)
        self.ligneQuatre.set_text(text)

        if avion.papa.etatFrequence in ['nextCoord', 'nextShoot']:
            freq = avion.papa.nextFrequency
        else:
            freq = '               '

        text = ('RMRS                                                 ' + freq + '         '
                + avion.papa.nextSector)
        self.ligneCinq.set_text(text)

    def kill(self):
        self.window.kill()

    def checkAlive(self):
        return self.window.alive()