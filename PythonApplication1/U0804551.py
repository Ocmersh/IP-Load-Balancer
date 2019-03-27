#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,set_ev_cls,CONFIG_DISPATCHER
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet,ethernet,arp,ipv4,ipv6
from ryu.lib.of_config import *

class IPLoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(IPLoadBalancer, self).__init__(*args, **kwargs)
        self.portMac = {}
        self.backList = []
        self.frontList = []
        self.frontList.append({"10.0.0.1":"00:00:00:00:00:01",'port':1})
        self.frontList.append({"10.0.0.2":"00:00:00:00:00:02",'port':2})
        self.frontList.append({"10.0.0.3":"00:00:00:00:00:03",'port':3})
        self.frontList.append({"10.0.0.4":"00:00:00:00:00:04",'port':4})
        self.backList.append({"10.0.0.5":"00:00:00:00:00:05",'port':5})
        self.backList.append({"10.0.0.6":"00:00:00:00:00:06",'port':6})
        self.current = backList[0]
        self.next = backList[0]
        self.virtualIP = "10.0.0.15"



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def currentPacket(self, ev):
        messageIn = ev.msg
        dpath = messageIn.datapath
        opflow = dpath.ofproto
        opParse = dpath.ofproto_parser
        sourcePort = messageIn.match['in_port']
        packetData = packet.Packet(messageIn.data)
        ethProt = packetData.get_protocol(ethernet.ethernet)

        dst = ethProt.dst
        src = ethProt.src
        self.portMac.setdefault(dpath.id, {})
        self.portMac[dpath.id][src] = sourcePort

        #self.addToTable()
        

        #arpProt = packetData.get_protocol(arp.arp)
        #arpdst = arpProt.dst
        #arpsrc = arpProt.src
        #arpmacdest = ethProt.src

        #loop through server list round robin
        #setnext


        #self.current = self.next

        ##############
        if dst in self.portMac[dpath.id]:
            out_port = self.portMac[dpath.id][dst]
        else:
            out_port = opflow.OFPP_FLOOD
        actions = [opParse.OFPActionOutput(out_port)]
        data = None
        if messageIn.buffer_id == opflow.OFP_NO_BUFFER:
            data = messageIn.data
            
        self.portMac[dpath.id][src] = sourcePort
        out = opParse.OFPPacketOut(datapath=dpath, buffer_id=messageIn.buffer_id,in_port=sourcePort, actions=actions, data=data)
        dpath.send_msg(out)
        ###############

    def addToTable(dpath, packetData, ethProt, opParse, opflow, sourcePort):
        x =1

    def messageForward():
        x =1

