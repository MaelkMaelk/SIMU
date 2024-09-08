from typing import Iterable
import pygame
import math
import pygame_gui
import interface

plotSize = 6
radarRefresh = 4
timeConstant = radarRefresh / 3600
listeEtrangers = ['G2', 'M2']
etiquetteLines = 4
nmToFeet = 6076
axe = 74
axePoint = 'BST'


def positionAffichage(x, y, zoom, scrollX, scrollY):
    """
    :param x: position en x
    :param y: position en y
    :param zoom: coefficient d'élargissement des distances
    :param scrollX: décalage en x
    :param scrollY: décalage en y
    :return: x, y pour l'affichage
    """

    x = x * zoom + scrollX
    y = y * zoom + scrollY
    return x, y


class Avion:

    global timeConstant
    global plotSize

    def __init__(self, Id, papa):
        self.Id = Id
        self.papa = papa
        self.bouton = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.papa.x, self.papa.y), (20, 20)), text='')
        self.bouton.generate_click_events_from: Iterable[int] = frozenset(
            [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT, pygame.BUTTON_MIDDLE])

        # Radar display
        self.drawRoute = False
        self.visible = True

        # etiquette
        self.etiquetteX = papa.x + 60
        self.etiquetteY = papa.y - 60
        self.etiquettePos = 0

        # Zoom & scroll
        self.affX = 0
        self.affY = 0

        # init de l'étiquette
        self.etiquette = interface.etiquetteAPS(self)

    def positionEtiquette(self):
        """On place l'étiquette dans une des positions possibles (NE, NO, SE, SO)"""

        value = 45  # distance de l'etiquette par rapport au plot
        if self.etiquettePos % 4 == 0:
            self.etiquetteX = self.affX + plotSize + value
            self.etiquetteY = self.affY + plotSize - value
        elif self.etiquettePos % 4 == 1:
            self.etiquetteX = self.affX + plotSize + value
            self.etiquetteY = self.affY + plotSize + value
        elif self.etiquettePos % 4 == 2:
            self.etiquetteX = self.affX + plotSize - value
            self.etiquetteY = self.affY + plotSize + value
        else:
            self.etiquetteX = self.affX + plotSize - value
            self.etiquetteY = self.affY + plotSize - value

    def drawVector(self, color, window, vecteurSetting, zoom):
        """

        :param color: quelle couleur pour le vecteur ?
        :param window: quelle surface ? (mettre la surface qu'on utilise pour pygame)
        :param vecteurSetting: int à combien de minutes on doit les dessiner
        :param zoom: niveau de zoom de la fenêtre
        :return: rien
        """
        for i in range(1, vecteurSetting + 1):

            pygame.draw.line(window, color, (self.affX + plotSize, self.affY + plotSize), (
                self.affX + plotSize + self.papa.speedPx * 60 / radarRefresh * vecteurSetting * zoom * math.cos(
                    self.papa.headingRad),
                self.affY + plotSize + self.papa.speedPx * 60 / radarRefresh * vecteurSetting * zoom * math.sin(
                    self.papa.headingRad)), 1)

            pygame.draw.circle(window, color, (self.affX + plotSize +
                                            self.papa.speedPx * 60 / radarRefresh * i * zoom * math.cos(
                self.papa.headingRad),
                                            self.affY + plotSize +
                                            self.papa.speedPx * 60 / radarRefresh * i * zoom * math.sin(
                                                self.papa.headingRad)),
                               2)

    def draw(self, win, zoom, scroll, vecteurs, vecteurSetting, typeAff):
        # updates
        self.affX = self.papa.x - plotSize
        self.affY = self.papa.y - plotSize

        self.positionEtiquette()  # on détermine la position de l'étiquette
        self.etiquette.update(self)  # on l'update via la fonction de l'étiquette

        # Dessin
        if self.visible:
            if self.papa.warning:
                color = (255, 120, 60)
            elif self.papa.part:
                color = (30, 144, 255)
            else:
                color = (255, 255, 255)

            pygame.draw.rect(win, color, (self.affX, self.affY, plotSize * 2, plotSize * 2), 1)

            if vecteurs or self.papa.warning:  # si on doit dessiner les vecteurs
                self.drawVector(color, win, vecteurSetting, zoom)  # on appelle la fonction

            radius = 1
            for plot in self.papa.comete:
                affPlot = [(plot[0] - plotSize) * zoom + plotSize + scroll[0],
                           (plot[1] - plotSize) * zoom + plotSize + scroll[1]]
                pygame.draw.circle(win, color, affPlot, int(round(radius)), 1)
                radius += 0.7
            pygame.draw.line(win, (255, 255, 255), (self.affX + plotSize, self.affY + plotSize),
                             (self.etiquetteX, self.etiquetteY))

    def update(self, papa, zoom, scroll):

        self.papa = papa

        # bouton
        self.bouton.rect = pygame.Rect((self.affX, self.affY), (20, 20))
        self.bouton.rebuild()

        self.bouton.rect = pygame.Rect((self.affX, self.affY), (20, 20))
        self.bouton.rebuild()

    def kill(self):
        self.bouton.kill()
        self.etiquette.kill()


class NouvelAvionWindow:

    def __init__(self, routes, avions):
        routes = [route for route in routes.values() if route['type'] in ['SID', 'STAR','TRANSIT']]
        self.routesFull = routes  # on s'en sert que pour avoir les valeurs de spawn/last au moment de l'apparition
        self.routes = routes
        self.avions = avions

        self.window = pygame_gui.elements.UIWindow(pygame.Rect((250, 250), (600, 400)))
        self.scrollRoutes = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (200, 400)),
                                                                     container=self.window)
        self.scrollAvions = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 0), (200, 200)),
                                                                     container=self.window,
                                                                     anchors={'left': 'left',
                                                                              'left_target': self.scrollRoutes})

        self.routesBoutons = []
        self.routesBoutons.append(pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (200, 15)),
            text=self.routes[0]['nom'],
            container=self.scrollRoutes))

        for route in self.routes[1:]:
            self.routesBoutons.append(pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (200, 15)),
                text=route['nom'],
                container=self.scrollRoutes, anchors={'top': 'top', 'top_target': self.routesBoutons[-1]}))

        self.avionsBoutons = []
        self.avionsBoutons.append(pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            text=list(avions.keys())[0],
            container=self.scrollAvions))

        for avion in list(avions.keys())[1:]:
            self.avionsBoutons.append(pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (200, 17)),
                text=avion,
                container=self.scrollAvions, anchors={'top': 'top', 'top_target': self.avionsBoutons[-1]}))
        self.conflitsBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 20), (200, 17)),
            text='Générateur de conflits',
            container=self.window, anchors={'top': 'top', 'top_target': self.scrollAvions, 'left': 'left',
                                            'left_target': self.scrollRoutes})
        self.validationBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 5), (200, 17)),
            text='Ok',
            container=self.window, anchors={'top': 'top', 'top_target': self.conflitsBouton, 'left': 'left',
                                            'left_target': self.scrollRoutes})

        self.indicatiflabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 0), (200, 17)),
                                                          container=self.window,
                                                          anchors={'left': 'left', 'left_target': self.scrollAvions},
                                                          text='Indicatif')
        self.indicatifinput = pygame_gui.elements.UITextEntryBox(relative_rect=pygame.Rect((0, 0), (200, 30)),
                                                                 container=self.window,
                                                                 anchors={'left': 'left',
                                                                          'left_target': self.scrollAvions,
                                                                          'top': 'top',
                                                                          'top_target': self.indicatiflabel})
        self.FLlabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 0), (200, 17)),
                                                   container=self.window,
                                                   anchors={'left': 'left', 'left_target': self.scrollAvions,
                                                            'top': 'top',
                                                            'top_target': self.indicatifinput},
                                                   text='FL')
        self.FLinput = pygame_gui.elements.UITextEntryBox(relative_rect=pygame.Rect((0, 0), (200, 30)),
                                                          container=self.window,
                                                          anchors={'left': 'left', 'left_target': self.scrollAvions,
                                                                   'top': 'top',
                                                                   'top_target': self.FLlabel})
        self.PFLlabel = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 0), (200, 17)),
                                                    container=self.window,
                                                    anchors={'left': 'left', 'left_target': self.scrollAvions,
                                                             'top': 'top',
                                                             'top_target': self.FLinput},
                                                    text='PFL')
        self.PFLinput = pygame_gui.elements.UITextEntryBox(relative_rect=pygame.Rect((0, 0), (200, 30)),
                                                           container=self.window,
                                                           anchors={'left': 'left', 'left_target': self.scrollAvions,
                                                                    'top': 'top',
                                                                    'top_target': self.PFLlabel})

    def kill(self):
        self.window.kill()


class MenuATC:

    def __init__(self, Idtuple, x, y):
        self.Idtuple = Idtuple
        self.window = pygame_gui.elements.UIWindow(pygame.Rect((x, y), (100, 250)))

        self.partBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='PART',
            container=self.window)

        self.movBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='MVT',
            container=self.window, anchors={'top': 'top', 'top_target': self.partBouton})

        self.FLBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='FL?',
            container=self.window, anchors={'top': 'top', 'top_target': self.movBouton})

        self.montrerBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 17)), text='Montrer',
            container=self.window, anchors={'top': 'top', 'top_target': self.FLBouton})

    def kill(self):
        self.window.kill()
        return self.Idtuple

