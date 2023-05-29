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

from ryu.base import app_manager
from ryu.packet_in import event


def get_pktin_rate(app, dpid=None):
	rep = app.send_request(event.EventRateRequest(dpid))
	return rep.pktin_rate

def get_pktin_num(app, dpid=None):
	rep = app.send_request(event.EventNumRequest(dpid))
	return rep.pktin_num

app_manager.require_app('ryu.packet_in.packet_in', api_style=True)