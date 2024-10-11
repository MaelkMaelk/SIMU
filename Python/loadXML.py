

# Native imports
import xml.etree.ElementTree as ET


def loadSegmentsXML(tree):

    dictSeg = {}

    for segment in tree.find('segments'):
        condition = None
        nom = segment.find('nom').text
        points = []

        XPT = None
        EPT = None
        repli = None

        if segment.find('repli') is not None:
            repli = segment.find('repli').text

        if segment.find('condition') is not None:
            zone = segment.find('condition').find('zone').text
            actif = segment.find('condition').find('active').text == 'True'

            condition = (zone, actif)

        for point in segment.findall('point'):
            pointDict = {}
            pointDict.update({'name': point.find('name').text})

            for XMLpoint in point:
                try:
                    XMLpointValue = int(XMLpoint.text)
                except:
                    XMLpointValue = XMLpoint.text

                    if XMLpoint.tag == 'XPT':
                        XMLpointValue = bool(XMLpoint.text)

                        if XMLpointValue:
                            XPT = point.find('name').text

                    if XMLpoint.tag == 'EPT':
                        XMLpointValue = bool(XMLpoint.text)

                        if XMLpointValue:
                            EPT = point.find('name').text

                pointDict.update({XMLpoint.tag: XMLpointValue})

            points.append(pointDict)

        dictSeg.update({nom: {'EPT': EPT,
                              'XPT': XPT,
                              'points': points,
                              'condition': condition,
                              'repli': repli,
                              'nom': nom}})

    return dictSeg

