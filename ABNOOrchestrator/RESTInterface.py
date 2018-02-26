__author__ = 'alejandroaguado'

import sys
import threading
import httplib2, httplib
import json

class RESTInterface(threading.Thread):

    def __init__(self, address, port, url, jsonstr):
        self.address = address
        self.port = port
        self.url=url
        self.jsonstr=jsonstr
        threading.Thread.__init__(self)

    def run(self):
        baseUrl = 'http://'+self.address+':'+str(self.port)+self.url
        h = httplib2.Http(".cache")
        #h.add_credentials('admin', 'admin')
        content=""
        # Get all the nodes/switches
        try:
            resp, content = h.request(baseUrl, "POST", headers={'Content-Type': 'application/json; charset=UTF-8'},body=self.jsonstr)
        except IOError, e:
            print "NETWORK UNREACHABLE: "+str(e.errno)
        return content

    def get(self):
        baseUrl = 'http://'+self.address+':'+str(self.port)+self.url
        h = httplib2.Http(".cache")
        #h.add_credentials('admin', 'admin')
        content=""
        # Get all the nodes/switches
        try:
            resp, content = h.request(baseUrl, "GET")
        except IOError, e:
            print "NETWORK UNREACHABLE: "+str(e.errno)
        return content

def request(url,method,jsn=None,user=None,passwd=None):
    import httplib2
    h = httplib2.Http(".cache")
    if user is not None and passwd is not None:
        h.add_credentials(user,passwd)
    body=""
    headers={}
    if jsn is not None:
        headers={'Content-Type': 'application/json; charset=UTF-8'}
        body=jsn
    resp, content = h.request(url, method, headers=headers,body=body)
    return content