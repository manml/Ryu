import sys
import ilib
sys.path.append("/home/mml/ryu")
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.dpid import str_to_dpid
from ryu.lib.packet import *

class SimpleSwitchIgmp13(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	_CONTEXTS = {'igmplib': ilib.IgmpLib}

	def __init__(self, *args, **kwargs):
		super(SimpleSwitchIgmp13, self).__init__(*args, **kwargs)
		self.mac_address_table = {}
		self._snoop = kwargs['igmplib']
		self._snoop.set_querier_mode(dpid=str_to_dpid('0000000000000001'), server_port=2)

	def add_flow(self,datapath,priority,match,actions,buffer_id=None):
		ofp = datapath.ofproto
		parser = datapath.ofproto_parser
		inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,actions)]
		flow = parser.OFPFlowMod(datapath=datapath,priority=priority,match=match,instructions=inst)
		datapath.send_msg(flow)

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		match = parser.OFPMatch()
		self.logger.info("Switch %s connected!",datapath.id)
		actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
		self.add_flow(datapath, 0, match, actions)
		match = parser.OFPMatch(eth_type = ether_types.ETH_TYPE_IPV6)
		actions = []
		self.add_flow(datapath,1,match,actions)

	@set_ev_cls(ilib.EventPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		in_port = msg.match['in_port']
		#print self._snoop._querier._mcast
		pkt = packet.Packet(msg.data)
		eth = pkt.get_protocols(ethernet.ethernet)[0]
		dst = eth.dst
		src = eth.src
		dpid = datapath.id
		pkt = packet.Packet(data=msg.data)
		ip_pkt = pkt.get_protocol(ipv4.ipv4)
		self.mac_address_table.setdefault(dpid, {})
		#self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
		if src in self.mac_address_table[dpid]:
			if in_port != self.mac_address_table[dpid][src]:
				return
		else:
			self.mac_address_table[dpid][src] = in_port
		if dst in self.mac_address_table[dpid]:
			out_port = self.mac_address_table[dpid][dst]
		else:
			out_port = ofproto.OFPP_FLOOD
		actions = [parser.OFPActionOutput(out_port)]
		if out_port != ofproto.OFPP_FLOOD:
			match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
			self.add_flow(datapath, 1, match, actions)
		data = None
		if msg.buffer_id == ofproto.OFP_NO_BUFFER:
			data = msg.data
		out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,in_port=in_port, actions=actions, data=data)
		datapath.send_msg(out)

	@set_ev_cls(ilib.EventMulticastGroupStateChanged,MAIN_DISPATCHER)
	def _status_changed(self, ev):
		msg = {
			ilib.MG_GROUP_ADDED: 'Multicast Group Added',
			ilib.MG_MEMBER_CHANGED: 'Multicast Group Member Changed',
			ilib.MG_GROUP_REMOVED: 'Multicast Group Removed',
			}
		self.logger.info("%s: [%s] querier:[%s] hosts:%s",msg.get(ev.reason), ev.address, ev.src,ev.dsts)