#!/usr/bin/python

import sys
sys.path.append("/home/mml/mininet")
import time
import os
from mininet.net import Mininet
from mininet.node import RemoteController,OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel

def topology(remoteip,ofversion):
	
	"***Create a network."
	net = Mininet(controller=RemoteController,switch=OVSSwitch)
	
	print("***Creating hosts")
	h1 = net.addHost("h1",mac="00:00:00:00:00:01",ip="192.168.1.1/16")
	h2 = net.addHost("h2",mac="00:00:00:00:00:02",ip="192.168.1.2/16")
	h3 = net.addHost("h3",mac="00:00:00:00:00:03",ip="192.168.1.3/16")
	h4 = net.addHost("h4",mac="00:00:00:00:00:04",ip="192.168.1.4/16")
	
	print("***Creating switches")
	s1 = net.addSwitch("s1",protocols=ofversion)
	s2 = net.addSwitch("s2",protocols=ofversion)
	s3 = net.addSwitch("s3",protocols=ofversion)
	s4 = net.addSwitch("s4",protocols=ofversion)
	
	c1 = net.addController("c1",controller=RemoteController,ip=remoteip,port=6653)
	c2 = net.addController("c2",controller=RemoteController,ip=remoteip,port=6654)

	print("***Create links")
	#switchLinkOpts = dict(bw=10,delay="1ms")
	#hostLinksOpts = dict(bw=100)
	
	net.addLink(s1, h1, 1)
	net.addLink(s2, h2, 1)
	net.addLink(s3, h3, 1)
	net.addLink(s4, h4, 1)
	net.addLink(s1, s2, 2,2)
	net.addLink(s2, s3, 3,2)
	net.addLink(s3, s4, 3,2)
	

	print("***Building network.")
	net.build()
	s1.start([c1])
	s2.start([c1])
	s3.start([c2])
	s4.start([c2])
	
	print("***Starting network")
	c1.start()
	c2.start()
	CLI(net)
	
	print("***Stoping network")
	net.stop()
	
if __name__ == "__main__":
	setLogLevel("info")
	topology("127.0.0.1","OpenFlow13")
