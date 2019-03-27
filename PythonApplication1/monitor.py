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
        opParse = dpath.ofproto_parser
        packetData = packet.Packet(msg.data)
        ethProt = packetData.get_protocol(ethernet.ethernet)
        desto = ethProt.dst
        source = ethProt.src
        out = opParse.OFPPacketOut(datapath=dpath,in_port=msg.in_port,actions=actions)
        dpath.send_msg(out)

        #FORWARD PACKET
        #topath = dpath.ofproto_parser
        #actions = [topath.OFPActionOutput(opflow.OFPP_FLOOD)]
