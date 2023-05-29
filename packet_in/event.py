# Copyright (C) 2013 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys
from ryu.controller import handler
from ryu.controller import event

LOG = logging.getLogger(__name__)


class EventRateRequest(event.EventRequestBase):
	def __init__(self, dpid=None):
		super(EventRateRequest, self).__init__()
		self.dst = 'packet_in'
		self.dpid = dpid


class EventRateReply(event.EventReplyBase):
	def __init__(self, dst, packet_in_rate):
		super(EventRateReply, self).__init__(dst)
		self.pktin_rate = packet_in_rate


class EventNumRequest(event.EventRequestBase):
	def __init__(self, dpid=None):
		super(EventNumRequest, self).__init__()
		self.dst = 'packet_in'
		self.dpid = dpid


class EventNumReply(event.EventReplyBase):
	def __init__(self, dst, packet_in_num):
		super(EventNumReply, self).__init__(dst)
		self.pktin_num = packet_in_num


handler.register_service('ryu.packet_in.packet_in')
