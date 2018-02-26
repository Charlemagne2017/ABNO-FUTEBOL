__author__ = 'alejandroaguado'

import cherrypy
import threading
import json
from RESTInterface import RESTInterface
from random import randint
from Service import Service
import httplib2, httplib

class RestFullFuncs(object):

    def __init__(self, params, services):
        self.params=params
        self.services=services

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def ME2Eprovisioning(self):
        data=cherrypy.request.json
        vtid=data['id']
        response='{"connections":['
        for req in data['connections']:
            source=req['source']
            sport=req['sport']
            dest=req['dest']
            dport=req['dport']
            bandwidth=req['bandwidth']
            nwDst="unset"
            nwSrc="unset"
            if 'nwSrc' in req.keys():
                nwSrc=req['nwSrc']
            if 'nwDst' in req.keys():
                nwDst=req['nwDst']
            #first of all: PCE request (via REsT APi)
            ri=RESTInterface(self.params.pceaddress, self.params.pceport,"/pce/v0.0/rest/request", json.dumps(req))
            ret=ri.run()
            jsonret=json.loads(ret)#check error status
            id=self.generateID()
            request=self.generateRequest(ret[:-1],bandwidth,id, 1, nwSrc, nwDst)
            if ("Error" in jsonret) | ("Error" in jsonret['path'][0]):
                return '{"Error":"NOPATH found"}'
            ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request)
            ret=ri2.run()
            jsonret=json.loads(ret)
            if "OK" in jsonret['Status']:
                serv=Service(id,cherrypy.request.remote.ip,"E2EProvisioning", "PM", jsonret['id'],source,dest, sport, dport, request,nwSrc, nwDst, vtid)
                self.services[id]=serv
                print serv.toString()
                servjson=json.loads(serv.toJson())
                servjson['source']=source
                servjson['dest']=dest
                if ("unset" not in nwDst) and ("unset" not in nwSrc):
                    servjson['nwDst']=nwDst
                    servjson['nwSrc']=nwSrc
                response=response+json.dumps(servjson)+","
        return response[:-1]+'],"vtid":"'+vtid+'"}'


    @cherrypy.expose
    @cherrypy.tools.json_in()
    def E2Eservice(self):
        data=cherrypy.request.json
        id=self.generateID()
        ri0=RESTInterface("localhost", "8081","/tm/v0.0/rest/fulltopology","").get()
        print ri0
        ri=json.loads(ri0)
        request={}
        request['path']=data['path']
        request['id']=id
        request['Workflow']="E2Eprovisioning"
        request['bandwidth']=100
        request['vlan']=data['vlan']
        print json.dumps(request)
        ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",json.dumps(request)).run()
        print ri2
        return '{"Workflow":"E2EService","ID":"'+str(id)+'","from":"'+cherrypy.request.remote.ip+'","Status":"Service successfully finished"}'

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def E2Eprovisioning(self):
        data=cherrypy.request.json
        source=data['source']
        sport=data['sport']
        dest=data['dest']
        dport=data['dport']
        bandwidth=data['bandwidth']
        nwDst="unset"
        nwSrc="unset"
        wavelength="unset"
        if 'nwSrc' in data.keys():
            nwSrc=data['nwSrc']
        if 'nwDst' in data.keys():
            nwDst=data['nwDst']
        print "Test- Added wavelength to retrieve it from json"
        if 'wavelength' in data.keys():
            wavelength=data['wavelength']
        #first of all: PCE request (via REsT APi)
        print json.dumps(data)
        ri=RESTInterface(self.params.pceaddress, self.params.pceport,"/pce/v0.0/rest/request", json.dumps(data))
        ret=ri.run()
        jsonret=json.loads(ret)#check error status
        id=self.generateID()
        request=self.generateRequest(ret[:-1],bandwidth,id, 1, nwSrc, nwDst, wavelength)
        print "::::::::::::::::::::::::::::::::::::::::::::"
        print ret[:-1]
        print "-----------------------"
        print request
        print "::::::::::::::::::::::::::::::::::::::::::::"
        if "vlan" in data.keys():
            request=request[:-1]+',"vlan":'+data['vlan']+'}'
        if ("Error" in ret):
            return '{"Error":"NOPATH found"}'
        print request
        ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request)
        ret=ri2.run()
        jsonret=json.loads(ret)
        if "OK" in jsonret['Status']:
            # Test- Added wavelength o service
            serv=Service(id,cherrypy.request.remote.ip,"E2EProvisioning", "PM", jsonret['id'],source,dest, sport, dport, request, nwSrc, nwDst, wavelength)
            #serv=Service(id,cherrypy.request.remote.ip,"E2EProvisioning", "PM", jsonret['id'],source,dest, sport, dport, request, nwSrc, nwDst)
            self.services[id]=serv
            print serv.toString()
        return '{"Workflow":"'+serv.workflow+'","ID":"'+str(serv.id)+'","from":"'+serv.ip+'","Status":"E2EProvisioning successfully finished"}'

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def E2Edeletion(self):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        data=cherrypy.request.json
        opid=data['id']
        print opid
        for key in self.services.keys():
            print key
        print "looking for: "+str(opid)
        if opid in self.services.keys():
            service=self.services[opid]
            request=self.generateRequest("",0,service.forwardedID,2,"","")
            ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request)
            response=ri2.run()
            self.services.pop(opid,None)
            return '{"Service":'+str(opid)+',"Status":"Successfully deleted"}'
        else:
            return '{"Service":'+str(opid)+',"Error":"This service does not exist"}'
    @cherrypy.expose
    def E2EprovisioningWeb(self,var=None, **params):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        data=params
        source=data['source']
        sport=data['sport']
        dest=data['dest']
        dport=data['dport']
        bandwidth=int(data['bandwidth'])
        data['bandwidth']=bandwidth
        nwDst="unset"
        nwSrc="unset"
        if 'nwSrc' in data.keys():
            nwSrc=data['nwSrc']
        if 'nwDst' in data.keys():
            nwDst=data['nwDst']
        #first of all: PCE request (via REsT APi)
        print json.dumps(data)
        ri=RESTInterface(self.params.pceaddress, self.params.pceport,"/pce/v0.0/rest/request", json.dumps(data))
        ret=ri.run()
        jsonret=json.loads(ret)#check error status
        id=self.generateID()
        request=self.generateRequest(ret[:-1],bandwidth,id, 1, nwSrc, nwDst)
        print request
        print "PCE11:  "+ret
        if ("Error" in ret):
            return '{"Error":"NOPATH found"}'
        ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request)
        ret=ri2.run()
        jsonret=json.loads(ret)
        if "OK" in jsonret['Status']:
            serv=Service(id,cherrypy.request.remote.ip,"E2EProvisioning", "PM", jsonret['id'],source,dest, sport, dport, request, nwSrc, nwDst)
            self.services[id]=serv
            print serv.toString()
        return '{"Workflow":"'+serv.workflow+'","ID":"'+str(serv.id)+'","from":"'+serv.ip+'","Status":"E2EProvisioning successfully finished"}'

    @cherrypy.expose
    def E2EdeletionWeb(self,var=None, **params):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        #print cherrypy.request.params.get('id')
        opid=int(params['id'])
        print opid
        for key in self.services.keys():
            print key
        print "Deletion- looking for: "+str(opid)
        if opid in self.services.keys():
            service=self.services[opid]
            request=self.generateRequest("",0,service.forwardedID,2,"","")
            ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request)
            response=ri2.run()
            self.services.pop(opid,None)
            return '{"Service":'+str(opid)+',"Status":"Successfully deleted"}'
        else:
            return '{"Service":'+str(opid)+',"Error":"This service does not exist"}'

    @cherrypy.expose
    def E2EreplanningWeb(self,var=None, **params):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        #print cherrypy.request.params.get('id')
        opid=int(params['id'])
        print opid
        for key in self.services.keys():
            print key
        print "Replanning - looking for: "+str(opid)
        if opid in self.services.keys():
            service=self.services[opid]
            request=self.generateRequest("",0,service.forwardedID,3,"","","193999")
            ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/replan",request)
            response=ri2.run()
            #self.services.pop(opid,None)


            from RESTInterface import request
            js={"source":"openflow:169934858","sport":"1014","dest":"openflow:203489290","dport":"1010","bandwidth":0,"wavelength":"193900"}
            resp=request("http://localhost:8085/abno/v0.0/rest/E2Eprovisioning","POST",jsn=json.dumps(js))
            print "Test- establish short path:"
            print resp
            jsonret=json.loads(resp)
            print "ID:"
            print jsonret["ID"]
            #change packet flows at edge nodes
            #first edge node openflow:360287970189639683

            switchID="openflow:360287970189639683"
            ingress="15"
            egress="26"
            flowName="replanF1"
            flowNameAux="replanF1Aux"
            baseUrl = 'http://137.222.204.72:8181/restconf/operations/sal-flow:update-flow'
            #'{"input":{"original-flow":{"flow-name":"f3","match":{"in-port":"25","vlan-match":{"vlan-id":{"vlan-id":"57"}}}},"updated-flow":{"match":{"in-port":"26","vlan-match":{"vlan-id":{"vlan-id":"57"}}},"instructions": { "instruction": [ { "order": "0", "apply-actions": { "action": [ { "output-action": {"output-node-connector": "15"}, "order": "0" } ] } } ] }, "flow-name": "f3", "table_id": "0","installHw":"true"},"node":"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id=\"openflow:360287970189639683\"]"}}'
            jsonstr='{"input":{"original-flow":{"flow-name":"flow3602879701896396832515","match":{"in-port":"25","vlan-match":{"vlan-id":{"vlan-id":"57"}}}},"updated-flow":{"match":{"in-port":"26","vlan-match":{"vlan-id":{"vlan-id":"57"}}},"instructions":{"instruction":[{"order":"0","apply-actions":{"action":[{"output-action":{"output-node-connector":"15"},"order":"0"}]}}]},"flow-name":"flow3602879701896396832515","table_id":"0","installHw":"true"},"node":"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id=\\\"'+switchID+'\\\"]"}}'
            #jsonstr='{"input":{"original-flow":{"flow-name":"flow3602879701896396832515","match":{"in-port":"25","vlan-match":{"vlan-id":{"vlan-id":"57"}}}},"updated-flow":{"match":{"in-port":"26","vlan-match":{"vlan-id":{"vlan-id":"57"}}},"instructions":{"instruction":[{"order":"0","apply-actions":{"action":[{"output-action":{"output-node-connector":"15"},"order":"0"}]}}]},"flow-name":"flow3602879701896396832515","table_id":"0","installHw":"true"},"node":"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id=\"openflow:360287970189639683\"]"}}'
            jsonobj=json.loads(jsonstr)
            jsonstr=json.dumps(jsonobj)
            jsonstraux='{"input":{"original-flow":{"flow-name":"flow3602879701896396831525","match":{"in-port":"15","vlan-match":{"vlan-id":{"vlan-id":"57"}}}},"updated-flow":{"match":{"in-port":"15","vlan-match":{"vlan-id":{"vlan-id":"57"}}},"instructions":{"instruction":[{"order":"0","apply-actions":{"action":[{"output-action":{"output-node-connector":"26"},"order":"0"}]}}]},"flow-name":"flow3602879701896396831525","table_id":"0","installHw":"true"},"node":"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id=\\\"'+switchID+'\\\"]"}}'
            jsonobjaux=json.loads(jsonstraux)
            jsonstraux=json.dumps(jsonobjaux)
            h = httplib2.Http(".cache")
            h.add_credentials('admin','admin')

            resp, content = h.request(baseUrl, "POST", headers={'Content-Type': 'application/json; charset=UTF-8'},body=jsonstr)
            respaux, contentaux = h.request(baseUrl, "POST", headers={'Content-Type': 'application/json; charset=UTF-8'},body=jsonstraux)
            print "1. Response of Replaning packet flows::"
            print resp
            #print respaux
            #second edge node openflow:360287970189639684
            switchID="openflow:360287970189639684"
            ingress="8"
            egress="26"
            flowName="replanF2"
            flowNameAux="replanF2Aux"
            baseUrl = 'http://137.222.204.72:8181/restconf/operations/sal-flow:update-flow'
            #'{"input":{"original-flow":{"flow-name":"f3","match":{"in-port":"25","vlan-match":{"vlan-id":{"vlan-id":"57"}}}},"updated-flow":{"match":{"in-port":"26","vlan-match":{"vlan-id":{"vlan-id":"57"}}},"instructions": { "instruction": [ { "order": "0", "apply-actions": { "action": [ { "output-action": {"output-node-connector": "15"}, "order": "0" } ] } } ] }, "flow-name": "f3", "table_id": "0","installHw":"true"},"node":"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id=\"openflow:360287970189639683\"]"}}'
            jsonstr='{"input":{"original-flow":{"flow-name":"flow360287970189639684258","match":{"in-port":"25","vlan-match":{"vlan-id":{"vlan-id":"57"}}}},"updated-flow":{"match":{"in-port":"26","vlan-match":{"vlan-id":{"vlan-id":"57"}}},"instructions":{"instruction":[{"order":"0","apply-actions":{"action":[{"output-action":{"output-node-connector":"8"},"order":"0"}]}}]},"flow-name":"flow360287970189639684258","table_id":"0","installHw":"true"},"node":"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id=\\\"'+switchID+'\\\"]"}}'
            #jsonstr='{"input":{"original-flow":{"flow-name":"flow3602879701896396832515","match":{"in-port":"25","vlan-match":{"vlan-id":{"vlan-id":"57"}}}},"updated-flow":{"match":{"in-port":"26","vlan-match":{"vlan-id":{"vlan-id":"57"}}},"instructions":{"instruction":[{"order":"0","apply-actions":{"action":[{"output-action":{"output-node-connector":"15"},"order":"0"}]}}]},"flow-name":"flow3602879701896396832515","table_id":"0","installHw":"true"},"node":"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id=\"openflow:360287970189639683\"]"}}'
            jsonobj=json.loads(jsonstr)
            jsonstr=json.dumps(jsonobj)
            jsonstraux='{"input":{"original-flow":{"flow-name":"flow360287970189639684825","match":{"in-port":"8","vlan-match":{"vlan-id":{"vlan-id":"57"}}}},"updated-flow":{"match":{"in-port":"8","vlan-match":{"vlan-id":{"vlan-id":"57"}}},"instructions":{"instruction":[{"order":"0","apply-actions":{"action":[{"output-action":{"output-node-connector":"26"},"order":"0"}]}}]},"flow-name":"flow360287970189639684825","table_id":"0","installHw":"true"},"node":"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id=\\\"'+switchID+'\\\"]"}}'
            jsonobjaux=json.loads(jsonstraux)
            jsonstraux=json.dumps(jsonobjaux)

            resp, content = h.request(baseUrl, "POST", headers={'Content-Type': 'application/json; charset=UTF-8'},body=jsonstr)
            respaux, contentaux = h.request(baseUrl, "POST", headers={'Content-Type': 'application/json; charset=UTF-8'},body=jsonstraux)
            print "2. Response of Replaning packet flows::"
            print resp


            # delete previous packet flows:

            # update service
            # initial service data: {"path": [{"egress": "13", "ingress": "6", "switchID": "openflow:360287970189639681"}, {"egress": "25", "ingress": "15", "switchID": "openflow:360287970189639683"}, {"egress": "1", "ingress": "1007", "switchID": "openflow:203489290"}, {"egress": "1", "ingress": "3", "switchID": "openflow:186712074"}, {"egress": "1008", "ingress": "2", "switchID": "openflow:169934858"}, {"egress": "8", "ingress": "25", "switchID": "openflow:360287970189639684"}], "bandwidth": "0", "Workflow": "E2Eprovisioning", "id": "676768098", "wavelength": "unset"}
            # new service optical part: {"path": [{"egress": "1", "ingress": "1014", "switchID": "openflow:169934858"}, {"egress": "1010", "ingress": "2", "switchID": "openflow:203489290"}], "bandwidth": "0", "Workflow": "E2Eprovisioning", "id": "328713435", "wavelength": "193900"}

            service=self.services[opid]
            print "Service before replanning::"
            print service.request
            newPath='{"path":[{"egress": "13", "ingress": "6", "switchID": "openflow:360287970189639681"}, {"egress": "26", "ingress": "15", "switchID": "openflow:360287970189639683"}, {"egress": "1010", "ingress": "2", "switchID": "openflow:203489290"},{"egress": "1", "ingress": "1014", "switchID": "openflow:169934858"}, {"egress": "8", "ingress": "26", "switchID": "openflow:360287970189639684"}]'
            #newPathjsonobj=json.loads(newPath)
            id=self.generateID()
            request2=self.generateRequest(newPath,0,id, 1, "unset", "unset", "193900")
            service.request=request2
            #service["path"]='[{"egress": "13", "ingress": "6", "switchID": "openflow:360287970189639681"}, {"egress": "26", "ingress": "15", "switchID": "openflow:360287970189639683"}, {"egress": "1010", "ingress": "2", "switchID": "openflow:203489290"},{"egress": "1", "ingress": "1014", "switchID": "openflow:169934858"}, {"egress": "8", "ingress": "26", "switchID": "openflow:360287970189639684"}]'
            self.services[opid]=service
            print "new service:::::"
            print service

            # remove new optical path service
            print "3333"
            #self.services.pop(jsonret["ID"],None)

            key=0
            self.services.pop(int(jsonret["ID"]),None)
            '''
            for service in self.services.keys():
                if self.services[service]['id']==jsonret["ID"]:
                    key=service
                    break
            if key!=0:
                self.services.pop(key,None)
            '''
            print "Num of services:"
            print len(self.services)
            print jsonret["ID"]
            print self.services

            return '{"Service":'+str(opid)+',"Status":"Successfully replanned"}'
        else:
            return '{"Service":'+str(opid)+',"Error":"This service does not exist"}'


    @cherrypy.expose
    def ListServices(self):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        ret='{"Services":['
        empty=True
        for key in self.services.keys():
            empty=False
            ret=ret+self.services[key].toJson()+","
        if not empty:
            ret=ret[:-1]
        ret=ret+']}'
        return ret


    @cherrypy.expose
    def CreateARPTree(self):
        response=RESTInterface(self.params.pceaddress, self.params.pceport,"/pce/v0.0/rest/spantree", "").get()
        return RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/arptree",response).run()

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def recovery(self):
        print "Recovery Workflow started"
        data=cherrypy.request.json
        response=RESTInterface(self.params.pmaddress,self.params.pmport,"/pm/v0.0/rest/get_services_involved",json.dumps(data)).run()
        affected=json.loads(response)
        #for service in affected -> delete (PM)

        #if "MOBILITY" not in data['']: #we dont delete when mobility (just in case)
        for service in affected['services']:
            print "Service "+json.dumps(service)
            request=self.generateRequest("",0,service['id'],2,"","")
            RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request).run()
        #for service in affected -> path (PCE)
        #                        -> configure (PM)
        for service in affected['services']:
            response=RESTInterface(self.params.pceaddress, self.params.pceport,"/pce/v0.0/rest/request", self.generatePCErequest(service['source'],service['sport'],service['dest'],service['dport'])).run()
            jsonret=json.loads(response)#check error status
            print response
            id=self.getID(service['id'])
            nwsrc="unset"
            nwdst="unset"
            if "nwDst" in service.keys():
                nwdst=service['nwDst']
            if "nwSrc" in service.keys():
                nwsrc=service['nwSrc']
            request=self.generateRequest(response[:-1],100000000,id, 1, nwsrc, nwdst)
            if ("Error" in jsonret) | ("Error" in jsonret['path'][0]):
                return '{"Error":"NOPATH found"}'
            ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request)
            ret=ri2.run()
            jsonret=json.loads(ret)
            if "OK" in jsonret['Status']:
                serv=Service(id,cherrypy.request.remote.ip,"E2EProvisioning", "PM", jsonret['id'],service['source'],service['dest'], service['sport'], service['dport'], request,nwsrc, nwdst)
                self.services[id]=serv
                print serv.toString()

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def replanning(self):
        print "Recovery Workflow started"
        data=cherrypy.request.json
        response=RESTInterface(self.params.pmaddress,self.params.pmport,"/pm/v0.0/rest/get_services_involved",json.dumps(data)).run()
        print response
        affected=json.loads(response)
        #for service in affected -> delete (PM)

        for service in affected['services']:
            print "Service "+json.dumps(service)
            request=self.generateRequest("",0,service['id'],2,"","")
            RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request).run()

        #for service in affected -> path (PCE)
        #                        -> configure (PM)
        for service in affected['services']:
            r=self.generatePCErequest(service['source'],service['sport'],service['dest'],service['dport'])
            req=json.loads(r)
            xro={'dpid':data['body']['dpid'],'port':data['body']['port']}
            req['xro']=xro
            r=json.dumps(req)
            response=RESTInterface(self.params.pceaddress, self.params.pceport,"/pce/v0.0/rest/request", r).run()
            jsonret=json.loads(response)#check error status
            print response
            id=self.getID(service['id'])
            nwsrc="unset"
            nwdst="unset"
            if "nwDst" in service.keys():
                nwdst=service['nwDst']
            if "nwSrc" in service.keys():
                nwsrc=service['nwSrc']
            request=self.generateRequest(response[:-1],100000000,id, 1, nwsrc, nwdst)
            if ("Error" in jsonret) | ("Error" in jsonret['path'][0]):
                return '{"Error":"NOPATH found"}'
            #trik for faster recovery
            #recuest=json.loads(request)
            #first=recuest['path'].pop(0)
            #recuest['path'].append(first)
            #request=json.dumps(recuest)
            ###
            ri2=RESTInterface(self.params.pmaddress, self.params.pmport,"/pm/v0.0/rest/dispatch",request)
            ret=ri2.run()
            jsonret=json.loads(ret)
            if "OK" in jsonret['Status']:
                serv=Service(id,cherrypy.request.remote.ip,"E2EProvisioning", "PM", jsonret['id'],service['source'],service['dest'], service['sport'], service['dport'], request,nwsrc, nwdst)
                self.services[id]=serv
                print serv.toString()

    def getID(self, id):
        for key in self.services.keys():
            print str(id)+"="+str(self.services[key].forwardedID)
            if str(id) in str(self.services[key].forwardedID):
                return key

    def generateID(self):
        generated=False
        num=0
        while (not generated):
            num=randint(0,1000000000)
            if num not in self.services.keys():
                generated=True
        return num

    def generateRequest(self,path,bandwidth,id, op, nwSrc, nwDst, wavelength="unset"):
        ret=""
        if (op==1):
            if ("unset" in nwSrc) & ("unset" in nwDst):
                ret=path+',"bandwidth":"'+str(bandwidth)+'","wavelength":"'+wavelength+'","id":"'+str(id)+'","Workflow":"E2Eprovisioning"}'
            else:
                ret=path+',"bandwidth":"'+str(bandwidth)+'","nwSrc":"'+nwSrc+'","nwDst":"'+nwDst+'","wavelength":"'+wavelength+'","id":"'+str(id)+'","Workflow":"E2Eprovisioning"}'
        elif (op==2):
            ret='{"Workflow":"E2Edeletion","id":'+str(id)+'}'
        elif (op==3):
            ret='{"Workflow":"replanning","id":'+str(id)+'}'
        return ret

    def generatePCErequest(self, ingressS, ingressP, egressS, egressP):
        return '{"source":"'+ingressS+'","sport":"'+ingressP+'","dest":"'+egressS+'","dport":"'+egressP+'","bandwidth":100000000}'


class RestAPI(threading.Thread):
    def __init__(self, params, services):
        self.params=params
        self.services=services

    def begin(self):
        print self.params.address+":"+str(self.params.port)
        cherrypy.config.update({'server.socket_host': self.params.address,'server.socket_port': self.params.port,})
        cherrypy.quickstart(RestFullFuncs(self.params, self.services),"/abno/v0.0/rest/")