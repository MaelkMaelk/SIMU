

# Module Import

import pygame


def saveScreenshot(win, path):
    screencopy = win.copy()
    pygame.image.save(screencopy, path)
