#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,set_ev_cls,CONFIG_DISPATCHER
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet,ethernet,arp,ipv4,ipv6
from ryu.lib.of_config import *

class IPLoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    switchIP = "10.0.0.10"
    serverList = []
    clientList = []
    ip2mac = {}
    ip2port = {}
    currentHostIP = 0

    def __init__(self, *args, **kwargs):
        super(IPLoadBalancer, self).__init__(*args, **kwargs)
        #add custom config to server list
        self.serverList.append({'ip':"10.0.0.1",'10.0.0.1':1,'mac':"00:00:00:00:00:01",'port':1})
        self.currentHostIP = self.serverList[currentHost]['ip']



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def currentPacket(self, ev):
        inbound = ev.msg #
        packetData = packet.Packet(inbound.data)
        self.forwarding(inbound.datapath, packetData, packetData.get_protocol(ethernet.ethernet), inbound.datapath.ofproto_parser, inbound.datapath.ofproto, inbound.match['in_port'])
        
        #respond

        self.current = self.next

    def forwarding(self, currentPath, packet, Eprotocol, parsedData, openflow, in_port):
        x=1

