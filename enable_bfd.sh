#!/bin/bash
# bfd_local_dst_mac represents the mac address of peer interface for wlan0 interface
INTVAL=10
ovs-vsctl set interface wlan0 bfd:enable=true
ovs-vsctl set interface wlan0 bfd:bfd_local_dst_mac=04:f0:21:11:3d:82 -- set interface wlan0 bfd:min_rx=$INTVAL -- set interface wlan0 bfd:min_tx=$INTVAL
ovs-vsctl set interface wlan1 bfd:enable=true
ovs-vsctl set interface wlan1 bfd:bfd_local_dst_mac=04:f0:21:11:3d:81 -- set interface wlan1 bfd:min_rx=$INTVAL -- set interface wlan1 bfd:min_tx=$INTVAL
