#!/bin/sh
ip route add default via 10.0.0.2
vlc /home/mml/videos/bean.rmvb --sout '#transcode{vcodec=h264,acodec=mpga,ab=128,channels=2,samplerate=44100}:udp{dst=224.1.1.1:1234}' --sout-keep
