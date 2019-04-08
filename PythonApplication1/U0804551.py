#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet,ethernet,arp,ipv4,ipv6
from ryu import cfg

class IPLoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    switchIP = "10.0.0.10"
    front = 4
    back = 2
    serverList = []
    ip2mac = {}
    ip2port = {}
    currentHostIP = 0
    nextHostIP = 0

    def __init__(self, *args, **kwargs):
        super(IPLoadBalancer, self).__init__(*args, **kwargs)
        CONF = cfg.CONF
        CONF.register_opts([cfg.IntOpt('front',default=4,help=('Number of front end clients')),cfg.IntOpt('back',default=2,help=('Number of back end servers')), cfg.StrOpt('switchIP',default='10.0.0.10',help=('IP address of the switch'))])
        self.switchIP = CONF.switchIP

        if CONF.front+CONF.back < 99:
            self.front = CONF.front
            self.back = CONF.back
        else:
            if CONF.front > 49:
                self.front = 49
            else:
                self.front = CONF.front

            if CONF.back > 49:
                self.back = 49
            else:
                self.back = CONF.back

        for initFront in range(0,self.front):
            if initFront < 10:
                self.serverList.append(('10.0.0.{}'.format(initFront),'00:00:00:00:00:0{}'.format(initFront),initFront))
                self.ip2mac['10.0.0.{}'.format(initFront)] = '00:00:00:00:00:0{}'.format(initFront)
                self.ip2port['10.0.0.{}'.format(initFront)] = initFront
            else:
                self.serverList.append(('10.0.0.'.format(initFront),'00:00:00:00:00:{}'.format(initFront),initFront))
                self.ip2mac['10.0.0.{}'.format(initFront)] = '00:00:00:00:00:{}'.format(initFront)
                self.ip2port['10.0.0.{}'.format(initFront)] = initFront
        for initBack in range(self.front+1,self.front+1+self.back):
            if initBack+self.front < 10:
                self.serverList.append(('10.0.0.{}'.format(initBack),'00:00:00:00:00:0{}'.format(initBack+self.front),initBack+self.front))
                self.ip2mac['10.0.0.{}'.format(initFront)] = '00:00:00:00:00:0{}'.format(initFront)
                self.ip2port['10.0.0.{}'.format(initFront)] = initFront
            else:
                self.serverList.append(('10.0.0.'.format(initBack+self.front),'00:00:00:00:00:{}'.format(initBack+self.front),initBack+self.front))
                self.ip2mac['10.0.0.{}'.format(initBack+self.front)] = '00:00:00:00:00:{}'.format(initBack+self.front)
                self.ip2port['10.0.0.{}'.format(initBack+self.front)] = initBack+self.front

        self.currentHostIP = self.serverList[0]
        self.nextHostIP = self.serverList[0]
        
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def currentPacket(self, ev):
        inbound = ev.msg #
        packetData = packet.Packet(inbound.data)
        self.forwarding(inbound.datapath, packetData.get_protocol(ethernet.ethernet), packetData, inbound.datapath.ofproto, inbound.datapath.ofproto_parser, inbound.match['in_port'])
        self.returning(inbound.datapath, packetData.get_protocol(ethernet.ethernet), packetData, inbound.datapath.ofproto, inbound.datapath.ofproto_parser, inbound.match['in_port'])
       
        arpInbound = inbound.datapath.get_protocol(arp.arp)
        arpDestination = arpInbound.src_ip
        arpSource = arpInbound.dst_ip
        arpMac = packetData.src

        if arpInbound in self.serverList:
            inboundMac = self.ip2mac[arpSource]
        else:
            X=1
            #DO SOMETHING

        outProtocolE = ethernet.ethernet(arpMac, arpSource, ether_types.ETH_TYPE_ARP)
        outProtocolA = arp.arp(1, 0x0800, 6, 4, 2, inboundMac, arpSource, arpDestination, arpMac)
        newPacket = Packet()
        newPacket.add_protocol(outProtocolE)
        newPacket.add_protocol(outProtocolA)
        newPacket.serialize()
        outbound = [inbound.datapath.ofproto_parser.OFPActionOutput(inbound.datapath.ofproto.OFPP_IN_PORT)]
        outboundData = inbound.datapath.ofproto_parser.OFPPacketOUT(datapath=inbound.datapath, buffer_id=inbound.datapath.ofproto.OFP_NO_BUFFER, in_port=inbound.match['in_port'], actions=outbound, data=newPacket.data)
        inbound.datapath.send_msg(outboundData)
        self.current = self.next

    def forwarding(self, packet, currentPath, Eprotocol, openflow, parsedData, in_port):
        inbound = packet.get_protocol(arp.arp).src_ip
        if inbound in self.serverList:
            return;
        parsing = parsedData.OFPMatch(in_port=in_port,ipv4_dst=self.switchIP,eth_type=0x0800)
        outbound = [parsedData.OFPActionSetField(ipv4_src=self.switchIP),parsedData.OFPActionOutput(in_port)]
        intitiate = [parsedData.OFPInstructionActions(openflow.OFPIT_APPLY_ACTIONS, outbound)]
        outboundData = parsedData.OFPFlowMod(datapath=inbound,priority=0,buffer_id=openflow.OFP_NO_BUFFER, match=parsing, instructions=intitiate)
        currentPath.send_msg(outboundData)

    def returning(self, packet, currentPath, Eprotocol, openflow, parsedData, in_port):
        #TOEDIT
        parsing = parsedData.OFPMatch(in_port=in_port,ipv4_dst=self.switchIP,eth_type=0x0800)
        outbound = [parsedData.OFPActionSetField(ipv4_src=self.switchIP),parsedData.OFPActionOutput(in_port)]
        intitiate = [parsedData.OFPInstructionActions(openflow.OFPIT_APPLY_ACTIONS, outbound)]
        outboundData = parsedData.OFPFlowMod(datapath=inbound,priority=0,buffer_id=openflow.OFP_NO_BUFFER, match=parsing, instructions=intitiate)
        currentPath.send_msg(outboundData)

