#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet.packet import Packet
from ryu.lib.packet import packet,ethernet,arp,ether_types
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
    nextHostIP = 1

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

        for initFront in range(1,self.front+1):
            if initFront < 10:
                self.serverList.append(('10.0.0.{}'.format(initFront),'00:00:00:00:00:0{}'.format(initFront),initFront))
                self.ip2mac['10.0.0.{}'.format(initFront)] = '00:00:00:00:00:0{}'.format(initFront)
            else:
                self.serverList.append(('10.0.0.'.format(initFront),'00:00:00:00:00:{}'.format(initFront),initFront))
                self.ip2mac['10.0.0.{}'.format(initFront)] = '00:00:00:00:00:{}'.format(initFront)

            self.ip2port['10.0.0.{}'.format(initFront)] = initFront

        for initBack in range(self.front+1,self.front+self.back+1):
            if initBack < 10:
                self.serverList.append(('10.0.0.{}'.format(initBack),'00:00:00:00:00:0{}'.format(initBack),initBack))
                self.ip2mac['10.0.0.{}'.format(initBack)] = '00:00:00:00:00:0{}'.format(initBack)
            else:
                self.serverList.append(('10.0.0.{}'.format(initBack),'00:00:00:00:00:{}'.format(initBack),initBack))
                self.ip2mac['10.0.0.{}'.format(initBack)] = '00:00:00:00:00:{}'.format(initBack)

            self.ip2port['10.0.0.{}'.format(initBack)] = initBack

        self.currentHostIP = self.serverList[0]
        self.nextHostIP = 1

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def currentPacket(self, ev):
        inbound = ev.msg #
        packetData = packet.Packet(inbound.data)

        if packetData.get_protocol(ethernet.ethernet) == ether_types.ETH_TYPE_ARP:
            self.forwarding(inbound.datapath, packetData.get_protocol(ethernet.ethernet), packetData, inbound.datapath.ofproto, inbound.datapath.ofproto_parser, inbound.match['in_port'])
            self.returning(inbound.datapath, packetData.get_protocol(ethernet.ethernet), packetData, inbound.datapath.ofproto, inbound.datapath.ofproto_parser, inbound.match['in_port'])

            arpInbound = inbound.datapath.get_protocol(arp.arp)
            arpDestination = arpInbound.src_ip
            arpSource = arpInbound.dst_ip
            arpMac = packetData.src

            for request in range (self.front+1,self.front+self.back+1):
                if request-(self.front+1) < self.back:
                    if arpDestination == self.serverList[request]:
                        outBoundMac = self.ip2mac[arpSource]
                else:
                    outBoundMac = self.serverList[self.currentHostIP][1]

                    self.nextHostIP += 1
                    if self.nextHostIP > self.back:
                        self.nextHostIP = 1

                    break

            outEthernet = ethernet.ethernet(arpMac, arpSource, ether_types.ETH_TYPE_ARP)
            outArp = arp.arp(1, 0x0800, 6, 4, 2, outBoundMac, arpSource, arpDestination, arpMac)
            outPacket = Packet()
            outPacket.add_protocol(outEthernet)
            outPacket.add_protocol(outArp)
            outPacket.serialize()
            outbound = [inbound.datapath.ofproto_parser.OFPActionOutput(inbound.datapath.ofproto.OFPP_IN_PORT)]
            outboundData = inbound.datapath.ofproto_parser.OFPPacketOUT(datapath=inbound.datapath, buffer_id=inbound.datapath.ofproto.OFP_NO_BUFFER, in_port=inbound.match['in_port'], actions=outbound, data=outPacket.data)
            inbound.datapath.send_msg(outboundData)
            self.currentHostIP = self.nextHostIP

        return

    def forwarding(self, packet, currentPath, Eprotocol, openflow, parsedData, in_port):
        inbound = packet.get_protocol(arp.arp).src_ip

        for serverIp in range (self.front+1,self.front+self.back+1):
            if serverIp-(self.front+1) > self.back:
                break
            else:
                if inbound == self.serverList[serverIp][0]:
                    return

        parsing = parsedData.OFPMatch(in_port=in_port,ipv4_dst=self.switchIP,eth_type=0x0800)
        outbound = [parsedData.OFPActionSetField(ipv4_src=self.currentHostIP),parsedData.OFPActionOutput(self.ip2port[self.currentHostIP])]
        instructions = [parsedData.OFPInstructionActions(openflow.OFPIT_APPLY_ACTIONS, outbound)]
        outboundData = parsedData.OFPFlowMod(datapath=currentPath,priority=0,buffer_id=openflow.OFP_NO_BUFFER, match=parsing, instructions=instructions)
        currentPath.send_msg(outboundData)

    def returning(self, packet, currentPath, Eprotocol, openflow, parsedData, in_port):
        inbound = packet.get_protocol(arp.arp).src_ip
        parsing = parsedData.OFPMatch(in_port=self.ip2port[self.currentHostIP],ipv4_src=self.currentHostIP,ipv4_dst=inbound,eth_type=0x0800)
        outbound = [parsedData.OFPActionSetField(ipv4_src=self.switchIP),parsedData.OFPActionOutput(in_port)]
        instructions = [parsedData.OFPInstructionActions(openflow.OFPIT_APPLY_ACTIONS, outbound)]
        outboundData = parsedData.OFPFlowMod(datapath=currentPath,priority=0,buffer_id=openflow.OFP_NO_BUFFER, match=parsing, instructions=instructions)
        currentPath.send_msg(outboundData)