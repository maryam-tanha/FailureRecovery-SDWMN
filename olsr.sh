#!/bin/bash
#---------Interface Retrieval----------------------------------
PHY0=`cat /sys/class/net/wlan0/phy80211/name`
PHY1=`cat /sys/class/net/wlan1/phy80211/name`
PHY2=`cat /sys/class/net/wlan2/phy80211/name`
#---------- 1st interface configurationi -----------
iw wlan0 del
iw phy $PHY0 interface add wlan0 type ibss
iw phy $PHY0 interface add mon0  type monitor
ifconfig wlan0 mtu 1524 up
iw dev wlan0 ibss join PANDA36 5180 
ifconfig wlan0 10.1.2.1/24
iwconfig wlan0 txpower 0
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
#---------- 2nd interface configurationi -----------
iw wlan1 del
iw phy $PHY1 interface add wlan1 type ibss
iw phy $PHY1 interface add mon1  type monitor
ifconfig wlan1 mtu 1524 up
iw dev wlan1 ibss join PANDA40 5200
ifconfig wlan1 10.1.4.1/24
iwconfig wlan1 txpower 0
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
#---------- 3rd interface configurationi -----------
iw wlan2 del
iw phy $PHY2 interface add wlan2 type ibss
iw phy $PHY2 interface add mon2  type monitor
ifconfig wlan2 mtu 1524 up
iw dev wlan2 ibss join PANDA1 2412
ifconfig wlan2 10.1.3.1/24
iwconfig wlan2 txpower 0
iw dev wlan0 set bitrates legacy-5 mcs-5 0 
#---------- 3rd interface configuration (CH 157)-----------
ifconfig wlan1 192.168.0.216/24
wpa_supplicant -B -iwlan1 -c/etc/wpa_supplicant.conf -Dwext
