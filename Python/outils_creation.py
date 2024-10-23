
# Module imports
import pygame
import pygame_gui

# Imports fichiers
from Python.interface import scrollListGen, selectButtonInList


class menu_modifs_avion:

    def __init__(self, routes, avions, avion_tuple):

        nomRoute = list(routes.keys())[0]

        self.avion = avion_tuple[1]

        # la fenêtre du menu
        self.window = pygame_gui.elements.UIWindow(pygame.Rect((250, 250), (600, 400)),
                                                   window_display_title="Modifications à l'apparition")

        # la liste des types avion
        self.typeAvionContainer = pygame_gui.elements.UIScrollingContainer(pygame.Rect((0, 34), (150, 200)),
                                                                           container=self.window,
                                                                           allow_scroll_x=False)

        self.typeAvionBoutonListe = scrollListGen(
            list(avions.keys()), pygame.Rect((0, 0), (125, 17)), self.typeAvionContainer, False)[1]

        # les divers autres boutons et champs

        self.indicatiflabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer},
            text='Indicatif')

        self.indicatifinput = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((0, 0), (200, 30)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top',
                     'top_target': self.indicatiflabel})

        self.FLlabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top',
                     'top_target': self.indicatifinput},
            text='FL')

        self.FLinput = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((0, 0), (200, 30)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top', 'top_target': self.FLlabel})

        self.PFLlabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (200, 17)),
            container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top', 'top_target': self.FLinput},
            text='PFL')

        self.PFLinput = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((0, 0), (200, 30)), container=self.window,
            anchors={'left': 'left', 'left_target': self.typeAvionContainer, 'top': 'top', 'top_target': self.PFLlabel})

        self.supprimer = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 20), (200, 17)),
            text='Supprimer',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.typeAvionContainer, 'left': 'left',
                     'left_target': self.typeAvionContainer})

        self.validerBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 5), (200, 17)),
            text='Ok',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.supprimer, 'left': 'left',
                     'left_target': self.typeAvionContainer})

        self.arrivalBouton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 20), (200, 17)),
            text='Arrivée?',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.typeAvionContainer, 'left': 'left',
                     'left_target': self.validerBouton})

        self.CPDLC = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 5), (200, 17)),
            text='CPDLC',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.arrivalBouton, 'left': 'left',
                     'left_target': self.validerBouton})

        self.ExRVSM = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 5), (200, 17)),
            text='ExRVSM',
            container=self.window,
            anchors={'top': 'top', 'top_target': self.CPDLC, 'left': 'left',
                     'left_target': self.validerBouton})

        self.returnValues = {'indicatif': self.avion.indicatif,
                             'avion': self.avion.aircraft,
                             'arrival': self.avion.arrival,
                             'conflit': False,
                             'CPDLC': self.avion.CPDLC,
                             'FL': int(self.avion.altitude // 100),
                             'PFL': self.avion.PFL,
                             'ExRVSM': self.avion.ExRVSM}

        for bouton in self.typeAvionBoutonListe:
            if bouton.text == self.avion.aircraft:
                bouton.select()

        if self.avion.ExRVSM:
            self.ExRVSM.select()

        if self.avion.CPDLC:
            self.CPDLC.select()

        if self.avion.arrival:
            self.arrivalBouton.select()

        self.indicatifinput.set_text(self.avion.indicatif)
        self.FLinput.set_text(str(round(self.avion.altitude / 100)))
        self.PFLinput.set_text(str(self.avion.PFL))

    def checkEvent(self, event):

        """
        Vérifie si un des boutons ou textbox du menu a été pressé ou modifié, et modifie les données en conséquence
        :arg event: l'évenement qu'il faut vérifier
        :returns: le dictionaire de valeurs si on valide, None sinon
        """

        # on vérifie d'abord les champs de text
        if event.ui_element in self.typeAvionBoutonListe:

            selectButtonInList(self.typeAvionBoutonListe, event.ui_element)
            self.returnValues.update({'avion': event.ui_element.text})

        elif event.ui_element == self.arrivalBouton:
            self.returnValues['arrival'] = not self.returnValues['arrival']
            if not self.arrivalBouton.is_selected:
                self.arrivalBouton.select()
            else:
                self.arrivalBouton.unselect()

        elif event.ui_element == self.ExRVSM:
            self.returnValues['ExRVSM'] = not self.returnValues['ExRVSM']
            if not self.ExRVSM.is_selected:
                self.ExRVSM.select()
            else:
                self.ExRVSM.unselect()

        elif event.ui_element == self.CPDLC:
            self.returnValues['CPDLC'] = not self.returnValues['CPDLC']
            if not self.CPDLC.is_selected:
                self.CPDLC.select()
            else:
                self.CPDLC.unselect()

        elif event.ui_element == self.supprimer:
            if not self.supprimer.is_selected:
                self.supprimer.select()
                self.returnValues.update({'Remove': 'Remove'})
            else:
                self.supprimer.unselect()
                self.returnValues.pop('Remove')

        elif event.ui_element == self.validerBouton:
            self.window.kill()
            return self.returnValues

    def checkFields(self, event):

        # on vérifie le FL
        if event.ui_element == self.FLinput:
            try:
                self.returnValues.update({'FL': int(event.text)})

            except:  # si l'utilisateur rentre n'importe quoi, on remet à la valeur de base
                self.returnValues.update({'FL': 310})

        # on vérifie le PFL
        elif event.ui_element == self.PFLinput:
            try:
                self.returnValues.update({'PFL': int(event.text)})

            except:  # si l'utilisateur rentre n'importe quoi, on remet à la valeur du FL
                if 'FL' in self.returnValues:
                    self.returnValues.update({'PFL': self.returnValues['FL']})
                else:
                    self.returnValues.update({'PFL': 310})

        # on vérifie l'indicatif
        elif event.ui_element == self.indicatifinput:
            self.returnValues.update({'indicatif': event.text})

    def kill(self):
        self.window.kill()

    def checkAlive(self):
        return self.window.alive()
