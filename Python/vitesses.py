
# Native imports
from math import sqrt

ms_per_kt = 0.51444
feet_per_metre = 3.28

# Some useful constants

g = 9.81          # Acceleration due to gravity
R = 287           # Specific gas constant for air
L = 0.0065        # Lapse rate in K/m
T0 = 288.15     # ISA sea level temp in K
p0 = 101325     # ISA sea level pressure in Pa
k = 1.4         # k is a shorthand for Gamma, the ratio of specific heats for air
lss0 = sqrt(k*R*T0)  # ISA sea level speed sound


def compressible_pitot(M):
    """
    Renvoies un delta de pression en fonction d'un mach
    :param M:
    :return:
    """

    return (M*M*(k-1)/2 + 1) ** (k/(k-1)) - 1


def pitot_to_Mach(d):
    """
    Retourne un machNumber en fonction d'un delta de pression
    :param d:
    :return:
    """
    return sqrt(((d+1)**((k-1)/k) - 1)*2/(k-1))


def temperature(h):
    """
    Température en fonction de l'alti (bloquée à -56C)
    :param h:
    :return:
    """
    T = T0 - h*L
    if T <= 217.15:
        T = 217.15
    return T


def lss(h):
    """
    Vitesse du son en fonction de l'alti
    :param h:
    :return:
    """
    return sqrt(k*R*temperature(h))


def pressure(h):
    """
    Pression en fonction de l'alti
    :param h:
    :return:
    """
    return p0 * (temperature(h) / T0) ** (g / L / R)


def IAS_to_Mach(IAS, alti):

    """
    Converti une IAS en Mach
    :param IAS:
    :param alti:
    :return:
    """

    alti = alti / feet_per_metre
    IAS = IAS * ms_per_kt
    ps = pressure(alti)
    pd = compressible_pitot(IAS/lss0) * p0

    return pitot_to_Mach(pd / ps)


def mach_to_TAS(M, alti):
    """
    Converti un point de mach en TAS
    :param M:
    :param alti:
    :return:
    """
    alti = alti / feet_per_metre
    return lss(alti) * M / ms_per_kt


def TAS_to_IAS(TAS, alti):
    """
    Convertit une TAS en IAS, de façon très grossière
    :return:
    """

    return TAS - alti / 185

