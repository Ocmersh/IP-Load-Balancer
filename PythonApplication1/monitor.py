#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import ipv6

class L2Forwarding(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2Forwarding, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def curr_packet(self, ev):

        #GET MESSAGE DATA
        msg = ev.msg
        dpath = msg.datapath
        opflow = dpath.ofproto
        packetData = packet.Packet(msg.data)
        ethProt = packetData.get_protocol(ethernet.ethernet)
        desto = ethProt.dst
        source = ethProt.src
        
        #IDENTIFY PROT
        ARP = True
        IPV4 = False
        IPV6 = False
        temp = "0.0"
    
        #PRINT MESSAGE DATA
        print("Packet ( 0 ) Received on Port("+temp+"): Eth "+temp)

        if not ARP:
            print("ARP")
        if not IPV4:
            print("IPV4")
        if not IPV6:
            print("IPV6")

        print("From IP:"+temp)
        print("To   IP:"+temp)
        print("From MAC:"+temp)
        print("To   MAC:"+temp)

        if not ARP:
            print("NOT IPV4")
            print("NOT IPV6")
        if not IPV4:
            print("NOT ARP")
            print("NOT IPV6")
        if not IPV6:
            print("NOT IPV4")
            print("NOT ARP")

        print("ETH")
        print("From MAC:"+temp)
        print("To   MAC:"+temp)
        print("Controller Switch ("+temp)
        print("Address, Port: ('"+temp+"', "+temp+")")

        #FORWARD PACKET
        topath = dpath.ofproto_parser
        actions = [topath.OFPActionOutput(opflow.OFPP_FLOOD)]
        out = topath.OFPPacketOut(datapath=dpath,in_port=opflow.OFPP_ANY,actions=actions)
        dpath.send_msg(out)