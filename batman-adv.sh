#!/bin/bash
#---------Interface Retrieval---------------------------
PHY0=`cat /sys/class/net/wlan0/phy80211/name`
PHY1=`cat /sys/class/net/wlan1/phy80211/name`
PHY2=`cat /sys/class/net/wlan2/phy80211/name`
modprobe batman-adv
#---------------------
iw wlan0 del
iw phy $PHY0 interface add wlan0 type ibss
iw phy $PHY0 interface add mon0  type monitor
ifconfig wlan0 mtu 1524 up
iw dev wlan0 ibss join PANDA36 5180 
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
batctl if add wlan0
#-------------------------
iw wlan1 del
iw phy $PHY1 interface add wlan1 type ibss
iw phy $PHY1 interface add mon1  type monitor
ifconfig wlan1 mtu 1524 up
iw dev wlan1 ibss join PANDA40 5200
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
batctl if add wlan1
#--------------------------
iw wlan2 del
iw phy $PHY2 interface add wlan2 type ibss
iw phy $PHY1 interface add mon1  type monitor
ifconfig wlan2 mtu 1524 up
iw dev wlan2 ibss join PANDA1 2412 
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
batctl if add wlan2
#--------------------------
batctl if add eth0
ifconfig bat0 10.11.12.1/24 up
batctl bl 1
iwconfig wlan0 txpower 0
iwconfig wlan1 txpower 0
iwconfig wlan2 txpower 0
#-------Configuring an OOB Monitoring & Interface ---------- 
ifconfig mon0 up
ifconfig mon1 up
ifconfig eth0 up
ifconfig wlan3 192.168.0.216/24
wpa_supplicant -B -iwlan3 -c/etc/wpa_supplicant.conf -Dwext
