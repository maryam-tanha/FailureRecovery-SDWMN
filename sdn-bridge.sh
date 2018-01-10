#!/bin/bash
/etc/init.d/openvswitch-switch stop
export PATH=$PATH:/usr/local/share/openvswitch/scripts
ovs-ctl start
ovs-ctl --no-ovs-vswitchd start
ovs-ctl --no-ovsdb-server start

ifconfig wlan0 up
ifconfig wlan1 up
ifconfig wlan2 up
ifconfig eth0 0 
ovs-vsctl del-br br0
ovs-vsctl add-br br0
ifconfig br0 up
ovs-vsctl set bridge br0 protocols=OpenFlow13 other-config:datapath-id=0000000000000001
#ovs-vsctl set-manager ptcp:6632
ovs-vsctl add-port br0 wlan0
ovs-vsctl add-port br0 wlan1
ovs-vsctl add-port br0 wlan2
ovs-vsctl add-port br0 eth0
ovs-vsctl set-controller br0 tcp:192.168.0.111:6633
#ifconfig br0 192.168.0.211/24 up 
#ovs-vsctl set bridge br0 stp_enable=true
