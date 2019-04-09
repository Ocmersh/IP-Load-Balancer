#!/usr/bin/env python3

# Author: Bryce Hansen - U0804551
# Date:   April 8th, 2019
# Course: CS 4480, University of Utah, School of Computing
# Copyright: CS 4480 and Bryce Hansen - This work may not be copied for use in Academic Coursework.
#
# I, Bryce Hansen, certify that I wrote this code from scratch and did not copy it in part or whole from 
# another source.  Any references used in the completion of the assignment are cited in my README file.
#
# File Contents
#
#    [This simple load balancer can handle up to a total of 99 total servers and clients.]

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet.packet import Packet
from ryu.lib.packet import packet,ethernet,arp,ether_types
from ryu import cfg

class IPLoadBalancer(app_manager.RyuApp):
    # The switches default IP as well as the number of front and back servers
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    switchIP = "10.0.0.10"
    front = 4
    back = 2
    frontList = []
    backList = []
    ip2mac = {}
    ip2port = {}
    currentHostIP = 0
    nextHostIP = 1

    def __init__(self, *args, **kwargs):
        super(IPLoadBalancer, self).__init__(*args, **kwargs)
        #Import and format config file
        CONF = cfg.CONF
        CONF.register_opts([cfg.IntOpt('front',default=4,help=('Number of front end clients')),cfg.IntOpt('back',default=2,help=('Number of back end servers')), cfg.StrOpt('switchIP',default='10.0.0.10',help=('IP address of the switch'))])
        self.switchIP = CONF.switchIP

        # checks to see if the total of front + back servers is greater than 99, if so it will reduce them to under 99.
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

        #generates IP MAC and Port addresses to lists for the front and back servers. Also saves them to easily accessible sets.
        for initFront in range(1,self.front+1):
            if initFront < 10:
                self.frontList.append(('10.0.0.{}'.format(initFront),'00:00:00:00:00:0{}'.format(initFront),initFront))
                self.ip2mac['10.0.0.{}'.format(initFront)] = '00:00:00:00:00:0{}'.format(initFront)
            else:
                self.frontList.append(('10.0.0.'.format(initFront),'00:00:00:00:00:{}'.format(initFront),initFront))
                self.ip2mac['10.0.0.{}'.format(initFront)] = '00:00:00:00:00:{}'.format(initFront)

            self.ip2port['10.0.0.{}'.format(initFront)] = initFront

        for initBack in range(1,self.back+1):
            if self.front+initBack < 10:
                self.backList.append(('10.0.0.{}'.format(self.front+initBack),'00:00:00:00:00:0{}'.format(self.front+initBack),self.front+initBack))
                self.ip2mac['10.0.0.{}'.format(self.front+initBack)] = '00:00:00:00:00:0{}'.format(self.front+initBack)
            else:
                self.backList.append(('10.0.0.{}'.format(self.front+initBack),'00:00:00:00:00:{}'.format(self.front+initBack),self.front+initBack))
                self.ip2mac['10.0.0.{}'.format(self.front+initBack)] = '00:00:00:00:00:{}'.format(self.front+initBack)

            self.ip2port['10.0.0.{}'.format(self.front+initBack)] = self.front+initBack

        for x in range(len(self.frontList)):
            print (self.frontList[x])
        for x in range(len(self.backList)):
            print (self.backList[x])

        #current server is the first backend server
        self.currentHostIP = self.backList[0][0]
        self.nextHostIP = 1

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def currentPacket(self, ev):
        #get basic data from packet
        inbound = ev.msg #
        packetData = packet.Packet(inbound.data)
        tempPath = inbound.datapath
        tempProto = tempPath.ofproto
        parser = tempPath.ofproto_parser

        #send a response
        if packetData.get_protocol(ethernet.ethernet).ethertype == ether_types.ETH_TYPE_ARP:
            self.forwarding(packetData, tempPath, packetData.get_protocol(ethernet.ethernet), tempProto, parser, inbound.match['in_port'])

            #Get ARP info
            arpInbound = packetData.get_protocol(arp.arp)
            arpSource = arpInbound.dst_ip
            arpDestination = arpInbound.src_ip
            arpMac = packetData.get_protocol(ethernet.ethernet).src

            #If the ARP request is from the back servers, set to return to host's IP
            for request in range (0,self.back):
                if arpDestination == self.backList[request][0]:
                    outBoundMac = self.ip2mac[arpSource]
                    break
            else:
                outBoundMac = self.ip2mac[self.currentHostIP]

            #create new packet and send to decided IP
            outEthernet = ethernet.ethernet(arpMac, outBoundMac, ether_types.ETH_TYPE_ARP)
            outArp = arp.arp(1, 0x0800, 6, 4, 2, outBoundMac, arpSource, arpMac, arpDestination)
            outPacket = Packet()
            outPacket.add_protocol(outEthernet)
            outPacket.add_protocol(outArp)
            outPacket.serialize()
            outbound = [parser.OFPActionOutput(tempProto.OFPP_IN_PORT)]
            outboundData = parser.OFPPacketOUT(datapath=tempPath, buffer_id=tempProto.OFP_NO_BUFFER, in_port=inbound.match['in_port'], actions=outbound, data=outPacket.data)
            tempPath.send_msg(outboundData)

            #iterate to next back server
            self.currentHostIP = self.backList[self.nextHostIP][0]
            self.nextHostIP += 1
            if self.nextHostIP > self.back:
                self.nextHostIP = 1

        return

    #A return response that reverses the forward response
    def returning(self, inbound, packet, currentPath, Eprotocol, openflow, parsedData, in_port):
        #parse and return response
        parsing = parsedData.OFPMatch(in_port=self.ip2port[self.currentHostIP],ipv4_src=self.currentHostIP,ipv4_dst=inbound,eth_type=0x0800)
        outbound = [parsedData.OFPActionSetField(ipv4_src=self.switchIP),parsedData.OFPActionOutput(in_port)]
        instructions = [parsedData.OFPInstructionActions(openflow.OFPIT_APPLY_ACTIONS, outbound)]
        outboundData = parsedData.OFPFlowMod(datapath=currentPath,priority=0,buffer_id=openflow.OFP_NO_BUFFER, match=parsing, instructions=instructions)
        currentPath.send_msg(outboundData)

            #Forwards the ARP request to the next server
    def forwarding(self, packet, currentPath, Eprotocol, openflow, parsedData, in_port):
        inbound = packet.get_protocol(arp.arp).src_ip

        #if from back IP's, return
        for serverIp in range (0,self.back):
            if inbound == self.backList[serverIp][0]:
                return

        #parse and forward response
        parsing = parsedData.OFPMatch(in_port=in_port,ipv4_dst=self.switchIP,eth_type=0x0800)
        outbound = [parsedData.OFPActionSetField(ipv4_dst=self.currentHostIP),parsedData.OFPActionOutput(self.ip2port[self.currentHostIP])]
        instructions = [parsedData.OFPInstructionActions(openflow.OFPIT_APPLY_ACTIONS, outbound)]
        outboundData = parsedData.OFPFlowMod(datapath=currentPath,priority=0,buffer_id=openflow.OFP_NO_BUFFER, match=parsing, instructions=instructions)
        currentPath.send_msg(outboundData)
        self.returning(inbound, packet, currentPath, Eprotocol, openflow, parsedData, in_port)