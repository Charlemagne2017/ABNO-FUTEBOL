__author__ = 'alejandroaguado'

from xml.etree import ElementTree


class ABNOParameters:
    def __init__(self, filename):
        self.document = ElementTree.parse(filename)
        root = self.document.getroot()
        tag = self.document.find('abnoconfig')
        self.address=tag.attrib['address']
        self.port = int(tag.attrib['port'])
        tag = self.document.find('pceconfig')
        self.pceaddress = tag.attrib['address']
        self.pceport = int(tag.attrib['port'])
        tag = self.document.find('pmconfig')
        self.pmaddress = tag.attrib['address']
        self.pmport = int(tag.attrib['port'])
        #tag = self.document.find('properties')