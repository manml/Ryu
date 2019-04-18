#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import contextlib
import json
from ryu.lib import hub
from ryu.lib.hub import StreamServer

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Server(object):
	def __init__(self, *args):
		super(Server, self).__init__()
		self.clients = {} #client = controller
		self.server = StreamServer(('0.0.0.0', 8888), self._connect)
		self.topo = {}
		

	def _connect(self, socket, address):
		print 'connected address:%s' % str(address)
		
		with contextlib.closing(Client(socket)) as client:
			client.server = self  
			client_id = len(self.clients)+1 

			client.set_id(client_id)
			self.clients[client_id] = client
			client.start()

	def start(self):
		hub.spawn(self.monitor)
		print("Server start...")
		self.server.serve_forever()
		
	def monitor(self):
		while True:
			print self.topo
			hub.sleep(2)

class Client(object):
	def __init__(self, socket):
		super(Client, self).__init__()
		self.send_queue = hub.Queue(32) #controller and server send message
		self.status = True
		self.server = None  # connect to server
		self.socket = socket
		self.client_id = 0

	def set_id(self,client_id):
		self.client_id = client_id
		msg = json.dumps({
			'cmd': 'set_id',
			'client_id': client_id
		})
		self.send(msg)

	def send(self,msg):
		if self.send_queue:
			self.send_queue.put(msg)

	def send_msg(self):
		try:
			while self.status:
				message = self.send_queue.get()
				#message += '\n'
				self.socket.sendall(message)
				hub.sleep(0.1)
		finally:# disconnect
			self.send_queue = None

	def rece_msg(self):
		while self.status:
			try:
				message = self.socket.recv(128)
				if len(message) == 0:
					log.info("connection fail")
					self.status = False
					break
				while '\n' != message[-1]:
					message += self.socket.recv(128)
				data = message.split("\n")
				for temp in data:
					if len(temp) == 0:
						continue
					msg = json.loads(temp)#analyze message
					if msg['cmd'] == 'add_topo':
						dst_dpid = msg['dst_dpid']
						dst_port_no = msg['dst_port_no']
						src_dpid = msg['src_dpid']
						src_port_no = msg['src_port_no']
						if (src_dpid,dst_dpid) not in self.server.topo.keys():
							self.server.topo[(src_dpid,dst_dpid)] = (src_port_no,dst_port_no)
							print "Add topo :",src_dpid,dst_dpid,":",src_port_no,dst_port_no
				hub.sleep(0.1)
			except ValueError:
				print('Value error for %s, len: %d', message, len(message))

	def start(self):
		t1 = hub.spawn(self.send_msg)
		t2 = hub.spawn(self.rece_msg)
		hub.joinall([t1, t2])

	def close(self):
		self.status = False
		self.socket.close()

def main():
	Server().start()

if __name__ == '__main__':
	main()
