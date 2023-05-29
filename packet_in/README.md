内置Packet In性能测试模块
------
1.创建/ryu/ryu/packet_in目录，将所有文件放到该目录下。

2.为了注册CLI的选项，在ryu/ryu/cmd/manager.py里面引入packet in模块
```diff
  from ryu.base.app_manager import AppManager
  from ryu.controller import controller
  from ryu.topology import switches
+ from ryu.packet_in import packet_in
```
3.进入ryu主目录，重新安装Ryu,命令取决于具体python版本。我这里是python3.注意之后每次修改packet_in目录下的文件，都需要重新安装Ryu。

    python3 setup.py install

4.运行Ryu应用并启用packet in模块，例如simple_switch_13

    ryu-manager ryu/app/simple_switch_13.py --packet-in

5.运行mininet

    mn --topo linear,3 --mac --switch ovsk --controller remote

6.在host里手动创建一些流量，例如先设置好ARP再发送HTTP请求。以下命令是在mininet命令行中运行的
：

    h1 arp -s 10.0.0.24 11:11:11:11:11:11
    h1 curl 10.0.0.24:56
在host里还可以写shell脚本或者使用ab压测：
 
    #!/bin/sh
    a=60
    while [ true ]
    do
            echo 
            curl 10.0.0.24:$a --connect-timeout 1
            let a++
    done
    ------------------------------------
    ab -n 1000 -c 100 http://10.0.0.24

目前该模块并不提供host之间的连通性，如有需要，读者可以自行添加。  
参考：SDN控制器性能测试白皮书
https://www.sdnctc.com/home/views/default/resource/pdf/Performance.pdf
