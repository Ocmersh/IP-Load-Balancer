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
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def curr_packet(self, ev):

        msg = ev.msg
        dpath = msg.datapath
        opflow = dpath.ofproto
        opParse = dpath.ofproto_parser
        in_port = msg.match['in_port']
        packetData = packet.Packet(msg.data)
        ethProt = packetData.get_protocol(ethernet.ethernet)
        dst = ethProt.dst
        src = ethProt.src
        self.mac_to_port.setdefault(dpath.id, {})
        self.mac_to_port[dpath.id][src] = in_port
        if dst in self.mac_to_port[dpath.id]:
            out_port = self.mac_to_port[dpath.id][dst]
        else:
            out_port = opflow.OFPP_FLOOD
        actions = [opParse.OFPActionOutput(out_port)]
        data = None
        if msg.buffer_id == opflow.OFP_NO_BUFFER:
            data = msg.data
        self.mac_to_port[dpath.id][src] = in_port
        out = opParse.OFPPacketOut(datapath=dpath, buffer_id=msg.buffer_id,in_port=in_port, actions=actions, data=data)
        dpath.send_msg(out)
