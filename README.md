# FailureRecovery-SDWMN

Software Defined Networking (SDN) brings unprecedented opportunities for facilitating the management of Wireless Mesh Networks. This project focuses on developing a reactive recovery (restoration-based recovery) routing controller application on top of Ryu controller. The results from the SDN-based scenarios are compared with the ones from the most popular distributed routing protocols for WMNs in terms of throughput and recovery time from link failures. Also, the limitations of the protection-based recovery is discussed.

The components are as follows:

BaseTopology.png: Our base designed topology.

SDN configuration, OVS on the Mesh Routers (MRs): sdn-bridge.sh and sdn-backhaul.sh

Our developed restoration-based routing modules: network_aware.py, reactive_udp.py, and reactive_tcp.py 

Configuration of the routing protocols: batman-adv.sh, olsr.sh, and open11s.sh (the configurations of MR1)

Protection with BFD and FF group tables in SDN: enable_bfd.sh, GT_UDP.sh, and GT_TCP.sh


