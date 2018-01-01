## Ryu用组表实现组播 ##
1.创建一个无环拓扑，设置OpenFlow交换机的版本是OF1.3
```
mn --topo tree,3,2  --mac --switch ovs,protocols=OpenFlow13 --controller remote
```
2.启动Ryu控制器文件，因为我是在ryu目录外运行的程序，所以我修改了默认目录，读者可以修改目录为自己的ryu的主目录。

```
ryu-manager multiple.py

```
3.设置主机的网关，这个网关是谁不重要，因为不需要和外网通信。

```
ip route add default via 10.0.0.1
```

4.组播发送源需要一个视频文件，我的是rmvb格式的，不同的格式在vlc里面可能需要不同的编码方式，读者可以先使用图形界面发送一次得到一些参数再写进命令里。
发送命令：

```
vlc /home/mml/videos/bean.rmvb --sout '#transcode{vcodec=h264,acodec=mpga,ab=128,channels=2,samplerate=44100}:udp{dst=224.1.1.1:1234}' --sout-keep
```

5.接收命令：

```
vlc udp://@224.1.1.1:1234
```

**Note:发送者和接收者的shell分别对应server和c1。读者可自行修改。**
