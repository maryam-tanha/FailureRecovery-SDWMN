# Faculty of Engineering, University of Victoria, Canada, 2018
# Author: Maryam Tanha
# This code reuses a part of the code available at https://github.com/osrg/ryu/pull/55/commits/aa401aac6c21c263d7df234071ba2ba82301834f and change it to make it suitable to be used in a wireless mesh network. Actually due to MAC rewriting in each hop, we need to add the SetField actions to the flow entries of the flow tables.
#This is free a software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# It  is distributed in the hope that it will be helpful, but WITHOUT ANY WARRANTY; 

# GNU General Public License for more details.


import logging
import struct
from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

from ryu.controller import dpset
import copy

from ryu.controller.handler import set_ev_cls
import network_aware
import networkx as nx
from threading import Lock
from ryu.controller import handler





class Reactive_Recovery(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        "Network_Aware": network_aware.Network_Aware,
    }

    def __init__(self, *args, **kwargs):
        super(Reactive_Recovery, self).__init__(*args, **kwargs)
        self.network_aware = kwargs["Network_Aware"]
        self.mac_to_port = {}
        self.datapaths = {}
        self.dpid_port_mac = {}
        self.hosts = []
        
        # links   :(src_dpid,dst_dpid)->(src_port,dst_port)
        self.link_to_port = self.network_aware.link_to_port

        # {sw :[host1_ip,host2_ip,host3_ip,host4_ip]}
        self.access_table = self.network_aware.access_table

        # dpid->port_num (ports without link)
        self.access_ports = self.network_aware.access_ports
        self.graph = self.network_aware.graph
        self.G = self.network_aware.G
        self.flows = []
        #self.lock = Lock() 
        self.failed_link = None
    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def add_flow(self, dp, p, match, actions, idle_timeout=0, hard_timeout=0):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=dp, priority=p,
                                idle_timeout=idle_timeout,
                                hard_timeout=hard_timeout,
                                match=match, instructions=inst)
        dp.send_msg(mod)

    def install_flow_reactive(self, paths, flow_info):
        '''
            path=[dpid1, dpid2, dpid3...]
            flow_info=(eth_type, src_ip, dst_ip, in_port)
        '''
        path = paths[0]
        # first flow entry
        in_port = flow_info[3]
        assert path
        datapath_first = self.datapaths[path[0]]
        ofproto = datapath_first.ofproto
        parser = datapath_first.ofproto_parser
        out_port = ofproto.OFPP_LOCAL

        # inter_link
        if len(path) > 2:
            for i in xrange(1, len(path) - 1):
                port = self.get_link2port(path[i - 1], path[i])
                port_next = self.get_link2port(path[i], path[i + 1])
                if port:
                    src_port, dst_port = port[1], port_next[0]
                    datapath = self.datapaths[path[i]]
                    ofproto = datapath.ofproto
                    parser = datapath.ofproto_parser
                    actions = []

                    actions.append(parser.OFPActionSetField(eth_src=self.get_port_mac(path[i], port_next[0])))
                    actions.append(parser.OFPActionSetField(eth_dst=self.get_port_mac(path[i+1], port_next[1])))
                   
                    actions.append(parser.OFPActionOutput(dst_port))
                    match = parser.OFPMatch(
                        in_port=src_port,
                        eth_type=flow_info[0],
                        ipv4_src=flow_info[1],
                        ipv4_dst=flow_info[2])
                    self.add_flow(
                        datapath, 1, match, actions,
                        idle_timeout=10, hard_timeout=30)


        if len(path) > 1:
            # the  first flow entry
            port_pair = self.get_link2port(path[0], path[1])
            out_port = port_pair[0]

            parser = datapath_first.ofproto_parser
            ofproto = datapath_first.ofproto

            actions = []
            actions.append(parser.OFPActionSetField(eth_src=self.get_port_mac(path[0], port_pair[0])))
            actions.append(parser.OFPActionSetField(eth_dst=self.get_port_mac(path[1], port_pair[1])))
            actions.append(parser.OFPActionOutput(out_port))
            match = parser.OFPMatch(
                in_port=in_port,
                eth_type=flow_info[0],
                ipv4_src=flow_info[1],
                ipv4_dst=flow_info[2])
            self.add_flow(datapath_first,
                          1, match, actions, idle_timeout=10, hard_timeout=30)

            # the last hop: tor -> host
            datapath = self.datapaths[path[-1]]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            actions = []
            src_port = self.get_link2port(path[-2], path[-1])[1]
            dst_port = None

            for key in self.access_table.keys():
                if flow_info[2] == self.access_table[key]:
                    dst_port = key[1]
                    break
            actions.append(parser.OFPActionSetField(eth_src=flow_info[4]))
            actions.append(parser.OFPActionSetField(eth_dst=flow_info[5]))
            actions.append(parser.OFPActionOutput(dst_port))
            match = parser.OFPMatch(
                in_port=src_port,
                eth_type=flow_info[0],
                ipv4_src=flow_info[1],
                ipv4_dst=flow_info[2])

            self.add_flow(
                datapath, 1, match, actions, idle_timeout=10, hard_timeout=30)




    def install_flow(self, paths, flow_info, buffer_id, data):
        '''
            path=[dpid1, dpid2, dpid3...]
            flow_info=(eth_type, src_ip, dst_ip, in_port)
        '''
        path = paths[0]
        # first flow entry
        in_port = flow_info[3]
        assert path
        datapath_first = self.datapaths[path[0]]
        ofproto = datapath_first.ofproto
        parser = datapath_first.ofproto_parser
        out_port = ofproto.OFPP_LOCAL

        # inter_link
        if len(path) > 2:
            for i in xrange(1, len(path) - 1):
                port = self.get_link2port(path[i - 1], path[i])
                port_next = self.get_link2port(path[i], path[i + 1])
                if port:
                    src_port, dst_port = port[1], port_next[0]
                    datapath = self.datapaths[path[i]]
                    ofproto = datapath.ofproto
                    parser = datapath.ofproto_parser
                    actions = []

                    actions.append(parser.OFPActionSetField(eth_src=self.get_port_mac(path[i], port_next[0])))
                    actions.append(parser.OFPActionSetField(eth_dst=self.get_port_mac(path[i+1], port_next[1])))
                   
                    actions.append(parser.OFPActionOutput(dst_port))
                    match = parser.OFPMatch(
                        in_port=src_port,
                        eth_type=flow_info[0],
                        ipv4_src=flow_info[1],
                        ipv4_dst=flow_info[2])
                    self.add_flow(
                        datapath, 1, match, actions,
                        idle_timeout=10, hard_timeout=30)

                    # inter links pkt_out
                    msg_data = None
                    if buffer_id == ofproto.OFP_NO_BUFFER:
                        msg_data = data

                    out = parser.OFPPacketOut(
                        datapath=datapath, buffer_id=buffer_id,
                        data=msg_data, in_port=src_port, actions=actions)

                    datapath.send_msg(out)

        if len(path) > 1:
            # the  first flow entry
            port_pair = self.get_link2port(path[0], path[1])
            out_port = port_pair[0]

            parser = datapath_first.ofproto_parser
            ofproto = datapath_first.ofproto

            actions = []
            actions.append(parser.OFPActionSetField(eth_src=self.get_port_mac(path[0], port_pair[0])))
            actions.append(parser.OFPActionSetField(eth_dst=self.get_port_mac(path[1], port_pair[1])))
            actions.append(parser.OFPActionOutput(out_port))
            match = parser.OFPMatch(
                in_port=in_port,
                eth_type=flow_info[0],
                ipv4_src=flow_info[1],
                ipv4_dst=flow_info[2])
            self.add_flow(datapath_first,
                          1, match, actions, idle_timeout=10, hard_timeout=30)

            # the last hop: tor -> host
            datapath = self.datapaths[path[-1]]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            actions = []
            src_port = self.get_link2port(path[-2], path[-1])[1]
            dst_port = None

            for key in self.access_table.keys():
                if flow_info[2] == self.access_table[key]:
                    dst_port = key[1]
                    break
            actions.append(parser.OFPActionSetField(eth_src=flow_info[4]))
            actions.append(parser.OFPActionSetField(eth_dst=flow_info[5]))
            actions.append(parser.OFPActionOutput(dst_port))
            match = parser.OFPMatch(
                in_port=src_port,
                eth_type=flow_info[0],
                ipv4_src=flow_info[1],
                ipv4_dst=flow_info[2])

            self.add_flow(
                datapath, 1, match, actions, idle_timeout=10, hard_timeout=30)

            # first pkt_out
            actions = []
            actions.append(parser.OFPActionSetField(eth_src=self.get_port_mac(path[0], port_pair[0])))
            actions.append(parser.OFPActionSetField(eth_dst=self.get_port_mac(path[1], port_pair[1])))

            actions.append(parser.OFPActionOutput(out_port))
            
            parser = datapath_first.ofproto_parser
            msg_data = None
            if buffer_id == ofproto.OFP_NO_BUFFER:
                msg_data = data

            out = parser.OFPPacketOut(
                datapath=datapath_first, buffer_id=buffer_id,
                data=msg_data, in_port=in_port, actions=actions)

            datapath_first.send_msg(out)

            # last pkt_out
            datapath = self.datapaths[path[-1]]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            actions = []
            actions.append(parser.OFPActionSetField(eth_src=flow_info[4]))
            actions.append(parser.OFPActionSetField(eth_dst=flow_info[5]))

            actions.append(parser.OFPActionOutput(dst_port))  
            msg_data = None
            if buffer_id == ofproto.OFP_NO_BUFFER:
                msg_data = data

            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=buffer_id,
                data=msg_data, in_port=src_port, actions=actions)

            datapath.send_msg(out)
         ##*** not neede for our topo
        #else:  # src and dst on the same
        #    out_port = None
        #    actions = []
        #    for key in self.access_table.keys():
        #        if flow_info[2] == self.access_table[key]:
        #            out_port = key[1]
        #            break
  
        #    actions.append(parser.OFPActionOutput(out_port))
        #    match = parser.OFPMatch(
        #        in_port=in_port,
        #        eth_type=flow_info[0],
        #        ipv4_src=flow_info[1],
        #        ipv4_dst=flow_info[2])
        #    self.add_flow(
        #        datapath_first, 1, match, actions,
        #        idle_timeout=10, hard_timeout=30)
#
#            # pkt_out
 #           msg_data = None
 #           if buffer_id == ofproto.OFP_NO_BUFFER:
 #               msg_data = data
#
#            out = parser.OFPPacketOut(
#                datapath=datapath_first, buffer_id=buffer_id,
#                data=msg_data, in_port=in_port, actions=actions)

#            datapath_first.send_msg(out)


    @set_ev_cls(event.EventHostAdd)
    def _event_host_add_handler(self, ev):
        msg = ev.host.to_dict()
        self.hosts.append(copy.deepcopy(msg))


    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def _event_dp_handler(self, ev):
        dpid = ev.dp.id
       # self.logger.info('Learning ports'' MAC addresses of switch %d\n', dpid)
        self.dpid_port_mac[dpid] = []

        for port in ev.ports:
                tmp_dict = {}
                tmp_dict[port.port_no] = port.hw_addr
                self.dpid_port_mac[dpid].append(tmp_dict)
                #self.dpid_port_mac[dpid].append([port.port_no, port.hw_addr])
       # self.logger.info('List of port MAC addresses is %s\n', self.dpid_port_mac)
   

    def get_port_mac(self, dpid, port):
        associated_ports = self.dpid_port_mac[dpid]
        port_mac = 0
        for item in associated_ports:
                for pp in item:
                        if  port==pp:
                                port_mac = item[pp]
                                break
        return port_mac


 
    def get_host_location(self, host_ip):
        for key in self.access_table:
            if self.access_table[key] == host_ip:
                return key
        self.logger.debug("%s location is not found." % host_ip)
        return None


    def get_link2port(self, src_dpid, dst_dpid):
        if (src_dpid, dst_dpid) in self.link_to_port:
            return self.link_to_port[(src_dpid, dst_dpid)]
        else:
            self.logger.debug("Link to port is not found.")
            return None


    '''
    In packet_in handler, we need to learn access_table by ARP.
    Therefore, the first packet from UNKOWN host MUST be ARP.
    '''

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        
        eth_src = pkt.get_protocols(ethernet.ethernet)[0].src
        eth_dst = pkt.get_protocols(ethernet.ethernet)[0].dst

        eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if arp_pkt:
            arp_src_ip = arp_pkt.src_ip
            arp_dst_ip = arp_pkt.dst_ip

            # record the access info
            if in_port in self.access_ports[datapath.id]:
                self.access_table[(datapath.id, in_port)] = arp_src_ip

            result = self.get_host_location(arp_dst_ip)
            if result:  # host record in access table.
                datapath_dst, out_port = result[0], result[1]
                actions = [parser.OFPActionOutput(out_port)]
                datapath = self.datapaths[datapath_dst]

                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=ofproto.OFPP_CONTROLLER,
                    actions=actions, data=msg.data)
                datapath.send_msg(out)
            else:       # access info is not existed. send to all host.
                for dpid in self.access_ports:
                    for port in self.access_ports[dpid]:
                        if (dpid, port) not in self.access_table.keys():
                            actions = [parser.OFPActionOutput(port)]
                            datapath = self.datapaths[dpid]
                            out = parser.OFPPacketOut(
                                datapath=datapath,
                                buffer_id=ofproto.OFP_NO_BUFFER,
                                in_port=ofproto.OFPP_CONTROLLER,
                                actions=actions, data=msg.data)
                            datapath.send_msg(out)

        if isinstance(ip_pkt, ipv4.ipv4):

            ip_src = ip_pkt.src
            ip_dst = ip_pkt.dst

            result = None
            src_sw = None
            dst_sw = None 

            paths = []
            src_location = self.get_host_location(ip_src)
            dst_location = self.get_host_location(ip_dst)

            if src_location:
                src_sw = src_location[0]

            if dst_location:
                dst_sw = dst_location[0]
            if self.graph == None:
                self.logger.info("Graph is empty.")
                self.network_aware.get_topology(None) # Reflesh the topology database.
            if src_sw not in self.G.nodes():
                self.network_aware.get_topology(None) # Reflesh the topology database.

            
            if src_sw != None and dst_sw != None:
                #self.G = self.network_aware.G
                paths = [nx.dijkstra_path(self.G, source=src_sw, target=dst_sw, weight=None)]
                self.logger.info("Path is %s", paths)
            else:
                self.network_aware.get_topology(None)


            if paths:
                install_flow_flag = True
                if self.hosts:
                        install_flow_flag = False
                        for h in self.hosts:
                                if h['mac'] == eth_dst or h['mac'] == eth_src:
                                        install_flow_flag = True
                                        break
                if not install_flow_flag:
                        return

                self.logger.info(" PATH[%s --> %s]:%s\n" % (ip_src, ip_dst, paths[0]))

                flow_info = [eth_type, ip_src, ip_dst, in_port, eth_src, eth_dst]
              
                flow ={}
                flow['info'] = flow_info
                flow['path'] = paths[0]
                if  flow  not in self.flows:
                	self.flows.append(flow)

                self.install_flow(paths, flow_info, msg.buffer_id, msg.data)
            else:
                # Reflesh the topology database.
                self.network_aware.get_topology(None)




    @handler.set_ev_cls(event.EventLinkDelete)
    def link_del_handler(self, ev):
         #self.lock.acquire()
         self.logger.info("Link down: "+ str(ev))
         link = ev.link
         src = link.src
         dst = link.dst
         removed_link = link
         tmp_list = []
         for l in self.network_aware.links:
         	if l != link:   
                	tmp_list.append(l)
   
         self.network_aware.update_topology(tmp_list)
         self.G = self.network_aware.G
         self.logger.info( "\t Removed link is %s \n", removed_link)
         if removed_link is not None and  (dst.dpid == 1  and src.dpid == 2) and (not self.failed_link):  ### failure of link 2 --> 1, only consider of the failure events
                        self.logger.info("Update topo\n")
                        self.failed_link =True
                        self.network_aware.update_topology(tmp_list)

                        self.G = self.network_aware.G
                        #print "delete flows" 


                        affected_flows = []
                        for f in self.flows:
                                if src.dpid in f['path']  and  dst.dpid in f['path']:
                                        affected_flows.append(f)
                        tmp_sw = []
                        for a in affected_flows:
                               for sw in a['path']:
                                        if sw not in tmp_sw:
                                                tmp_sw.append(sw)
                        for d in tmp_sw:
                        
                                self.network_aware.clearAllFlowsAndGroups(self.datapaths[d]) ## or only delete the related flows
                        for ff in self.flows:
                                if ff in affected_flows:
                                        self.flows.remove(ff)
                        self.logger.info("Affected flowssssssssss are %s\n", affected_flows)
                        for aa in affected_flows:
                                p = aa['path']
                                src_sw = p[0]
                                dst_sw = p[-1]
                                paths = [nx.dijkstra_path(self.G, source=src_sw, target=dst_sw, weight=None)]
                                self.install_flow_reactive(paths, aa['info'])
                                self.logger.info("Path is %s", paths[0])
                                #temp_list = list(reversed(paths[0]))
                                #self.install_flow_reactive([temp_list], aa['info'])
                                #self.logger.info("Path is %s", temp_list)

         		self.network_aware.get_topology(None)
        # self.lock.release()
