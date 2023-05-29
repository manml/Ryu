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
import time
import sys
from ryu.base import app_manager
from ryu.controller import handler
from ryu.lib import hub
from ryu.packet_in import event
from ryu.packet_in import packet_in

LOG = logging.getLogger(__name__)


class PerformanceTest(app_manager.RyuApp):

	_CONTEXTS = {
		'packet_in': packet_in.PacketIn,
	}
