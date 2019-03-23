#!/usr/bin/env python3


import random
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3, ether, inet
from ryu.lib.packet import packet, ethernet, ether_types, arp, tcp, ipv4, ipv6

class L2Forwarding(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2Forwarding, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def curr_packet(self, ev):

        msg = ev.msg
        dpath = msg.datapath
        ofproto = dpath.ofproto
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        dst = eth.dst
        src = eth.src
        
        ARP = True
        IPV4 = False
        IPV6 = False
        temp = "0.0"

        print("Packet ( 0 ) Received on Port("+temp+"): Eth "+temp)

        if ARP == true:
            print("ARP")
        if IPV4 == true:
            print("IPV4")
        if IPV6 == true:
            print("IPV6")

        print("From IP:"+temp)
        print("To   IP:"+temp)
        print("From MAC:"+temp)
        print("To   MAC:"+temp)

        if ARP == true:
            print("NOT IPV4")
            print("NOT IPV6")
        if IPV4 == true:
            print("NOT ARP")
            print("NOT IPV6")
        if IPV6 == true:
            print("NOT IPV4")
            print("NOT ARP")
        
        print("ETH")
        print("From MAC:"+temp)
        print("To   MAC:"+temp)
        print("Controller Switch ("+temp)
        print("Address, Port: ('"+temp+"', "+temp+")")

        out = ofp_parser.OFPPacketOut(datapath=dp,in_port=msg.in_port,actions=actions)
        dp.send_msg(out)
