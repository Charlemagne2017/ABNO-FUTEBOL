__author__ = 'alejandroaguado'

import json

class Service():

    def __init__(self, id, ip, workflow, forwarded, forwardedID, source, dest, sport, dport, request, nwSrc="unset",nwDst="unset", wavelength="unset", vtid="none"):
        self.id=id
        self.ip=ip
        self.workflow=workflow
        self.forwarded=forwarded
        self.forwardedID=forwardedID
        self.vtid=vtid
        self.source=source+"|"+str(sport)
        self.dest=dest+"|"+str(dport)
        self.request=request
        self.nwSrc=nwSrc
        self.nwDst=nwDst
        self.wavelength=wavelength

    def setVTID(self,vtid):
        self.vtid=""

    def toString(self):
        return "\tid: "+str(self.id)+"\n\tip: "+self.ip+"\n\tworkflow: "+self.workflow+"\n\tsent to: "+self.forwarded+"\n\tsenttoID: "+str(self.forwardedID)+"\n"

    def toJson(self):
        ret= '{"id":'+str(self.id)+',"owner":"'+self.ip+'","Workflow":"'+self.workflow+'", "source":"'+self.source+'","dest":"'+self.dest+'","path":'+json.dumps(json.loads(self.request)['path'])+'}'
        retjson=json.loads(ret)
        if ("unset" not in self.nwSrc) and ("unset" not in self.nwDst):
            retjson['nwDst']=self.nwDst
            retjson['nwSrc']=self.nwSrc
        return json.dumps(retjson)