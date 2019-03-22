from ryu.base import app_manager
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class L2Forwarding(app_manager.RyuApp):
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

        print("Packet Touched")

        out = ofp_parser.OFPPacketOut(datapath=dp,in_port=msg.in_port,actions=actions)
        dp.send_msg(out)