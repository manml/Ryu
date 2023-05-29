import logging
import six
import struct
import time
import sys
import psutil

from ryu import cfg

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.exception import RyuException
from ryu.lib import addrconv, hub
from ryu.lib.mac import DONTCARE_STR
from ryu.lib.dpid import dpid_to_str, str_to_dpid
from ryu.lib.port_no import port_no_to_str
from ryu.lib.packet import *
from ryu.ofproto.ether import ETH_TYPE_LLDP
from ryu.ofproto.ether import ETH_TYPE_CFM
from ryu.ofproto import nx_match
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import ofproto_v1_2
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_4
from ryu.packet_in import event


LOG = logging.getLogger(__name__)


CONF = cfg.CONF
CONF.log_opt_values(LOG,20)
CONF.register_cli_opt(
			cfg.BoolOpt('packet-in', default=False,
				 help='Calculate Packet In rate')
)




class PacketIn(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION, ofproto_v1_2.OFP_VERSION,
					ofproto_v1_3.OFP_VERSION, ofproto_v1_4.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(PacketIn, self).__init__(*args, **kwargs)

		self.name = 'packet_in'
		self.is_active = self.CONF.packet_in
		self.switch_list = []  # Swtich list
		self.pkin_total_num = 0 # Total packet-in number
		self.pkin_counts = {} #swtich packet-in number
		self.pkin_total_rate = 0 #store packet-in rate
		self.threads = []
		self.period = 1
		LOG.debug("Packet In Calculator Init")
		if self.is_active:
			self.threads.append(hub.spawn(self._get_rate))
		#hub.joinall(self.threads)
		
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def _switch_features_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		actions = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
		inst = [parser.OFPInstructionActions(type_=ofproto.OFPIT_APPLY_ACTIONS,actions=actions)]
		mod = parser.OFPFlowMod(datapath=datapath,priority=0,match=parser.OFPMatch(),instructions=inst)
		datapath.send_msg(mod)
		
		

	@set_ev_cls(ofp_event.EventOFPStateChange,
				[MAIN_DISPATCHER, DEAD_DISPATCHER])
	def state_change_handler(self, ev):
		dp = ev.datapath
		sw = dp.id
		assert dp is not None
		if ev.state == MAIN_DISPATCHER:
			self.pkin_counts[sw] = 0


	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def packet_in_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		sw = datapath.id
		self.switch_list.append(sw)
		self.pkin_counts[sw] += 1
		self.pkin_total_num += 1

		if ev.msg.msg_len < ev.msg.total_len:
			self.logger.debug("packet truncated: only %s of %s bytes",
							  ev.msg.msg_len, ev.msg.total_len)

		pkt = packet.Packet(msg.data)
		pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]


		eth_dst = pkt_eth.dst
		eth_src = pkt_eth.src

		in_port = msg.match['in_port']
		dpid = datapath.id

		pkt_arp = pkt.get_protocol(arp.arp)
		if pkt_arp:
			# Flow install
			self._handle_arp(datapath, pkt_eth, pkt_arp)

			#Packet Out
			actions = [parser.OFPActionOutput(in_port)]
			data = None
			if msg.buffer_id == ofproto.OFP_NO_BUFFER:
				data = msg.data
			out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,in_port=in_port, actions=actions, data=data)
			datapath.send_msg(out)

		pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
		if pkt_ipv4:
			if pkt_ipv4.proto == in_proto.IPPROTO_TCP:
				pkt_tcp = pkt.get_protocol(tcp.tcp)
				# Flow install
				self._handler_tcp(datapath,pkt_ipv4,pkt_tcp)

				#Packet Out
				actions = [parser.OFPActionOutput(in_port)]
				data = None
				if msg.buffer_id == ofproto.OFP_NO_BUFFER:
					data = msg.data
				out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,in_port=in_port, actions=actions, data=data)
				datapath.send_msg(out)


	def _handle_arp(self, datapath, pkt_eth, pkt_arp):
		#print("ARP Code = ",pkt_arp.opcode)
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		actions = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
		inst = [parser.OFPInstructionActions(type_=ofproto.OFPIT_APPLY_ACTIONS,actions=actions)]
		if pkt_arp.opcode == arp.ARP_REQUEST:
			mod = parser.OFPFlowMod(datapath=datapath,priority=1,match=parser.OFPMatch(arp_op=arp.ARP_REQUEST,eth_type=ether_types.ETH_TYPE_ARP,arp_spa=pkt_arp.src_ip,arp_tpa=pkt_arp.dst_ip),instructions=inst)
			datapath.send_msg(mod)
		elif pkt_arp.opcode == arp.ARP_REPLY:
			mod = parser.OFPFlowMod(datapath=datapath,priority=1,match=parser.OFPMatch(arp_op=arp.ARP_REPLY,eth_type=ether_types.ETH_TYPE_ARP,arp_spa=pkt_arp.src_ip,arp_tpa=pkt_arp.dst_ip),instructions=inst)
			datapath.send_msg(mod)

	def _handler_tcp(self, datapath, pkt_ipv4, pkt_tcp):
		#print('TCP src %s :%d dst %s:%d' %(pkt_ipv4.src, pkt_tcp.src_port,pkt_ipv4.dst,pkt_tcp.dst_port))
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		actions = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
		inst = [parser.OFPInstructionActions(type_=ofproto.OFPIT_APPLY_ACTIONS,actions=actions)]
		mod = parser.OFPFlowMod(datapath=datapath,priority=1,match=parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ip_proto=in_proto.IPPROTO_TCP,ipv4_src=pkt_ipv4.src,ipv4_dst=pkt_ipv4.dst,tcp_src=pkt_tcp.src_port,tcp_dst=pkt_tcp.dst_port),instructions=inst)
		datapath.send_msg(mod)



	def _get_rate(self):
		temp = 0
		LOG.debug("Start calculating------------")
		while self.is_active:
			LOG.info("------------------------------------------------")
			LOG.info("Total Packet-In number is : %d",self.pkin_total_num)
			self.pkin_total_rate = (self.pkin_total_num - temp) / self.period
			temp = self.pkin_total_num
			LOG.info("Current Packet-In PPS is : %d",self.pkin_total_rate)
			
			mem = psutil.virtual_memory()
			LOG.info(f"Current Memory Utilization is : {mem[2]}%")
			cpu = psutil.cpu_percent()
			LOG.info(f"Current CPU Utilization is : {cpu}%")

			hub.sleep(self.period)

	@set_ev_cls(event.EventNumRequest)
	def num_request_handler(self, req):
		LOG.debug("Event num Start -------")
		dpid = req.dpid
		pktin_num = 0
		if dpid is None:
			pktin_num = self.pkin_total_num
		elif dpid in self.switch_list:
			pktin_num = self.pkin_counts[dpid]

		rep = event.EventNumReply(req.src, pktin_num)
		self.reply_to_request(req, rep)

	@set_ev_cls(event.EventRateRequest)
	def rate_request_handler(self, req):
		LOG.debug("Event rate Start -------")
		rep = event.EventRateReply(req.src, self.pkin_total_rate)
		self.reply_to_request(req, rep)