#!/bin/bash
PHY0=`cat /sys/class/net/wlan0/phy80211/name`
PHY1=`cat /sys/class/net/wlan1/phy80211/name`
PHY2=`cat /sys/class/net/wlan2/phy80211/name`
#-------------------------
iw wlan0 del
iw phy $PHY0 interface add mesh0 type mp mesh_id PANDA36
iw phy $PHY0 interface add mon0  type monitor
iw dev mesh0 set channel 36
ifconfig mesh0 up
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
#-------------------------
iw wlan1 del
iw phy $PHY1 interface add mesh1 type mp mesh_id PANDA40
iw phy $PHY1 interface add mon1  type monitor
iw dev mesh1 set channel 40
ifconfig mesh1 up
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
#-------------------------
iw wlan2 del
iw phy $PHY2 interface add mesh2 type mp mesh_id PANDA1
iw phy $PHY2 interface add mon2  type monitor
iw dev mesh2 set channel 1
ifconfig mesh2 up
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
#-------------------------
brctl addbr br-lan
brctl addif br-lan mesh0
brctl addif br-lan mesh1
brctl addif br-lan mesh2
#brctl addif br-lan eth0
ifconfig br-lan 10.11.12.1/24 up
#-------------------------
iwconfig mesh0 txpower 0
iwconfig mesh1 txpower 0
iwconfig mesh2 txpower 0
ifconfig mon0 up
ifconfig mon1 up
ifconfig mon2 up
brctl stp br-lan on
ifconfig wlan3 192.168.0.216/24
wpa_supplicant -B -iwlan3 -c/etc/wpa_supplicant.conf -Dwext
