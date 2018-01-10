# This code extends the  module "network_aware" which is available at https://github.com/osrg/ryu/pull/55/commits/aa401aac6c21c263d7df234071ba2ba82301834f and change it to make it suitable to be used in a wireless mesh network. 
# Modified by: Maryam Tanha, Dec 2017 (Added functions: link_add_hanler, clearAllFlowsAndGroups, del_group, del_flow, find_failed_link)

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
from ryu.lib import hub

from ryu.controller import handler
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link


from ryu.controller import dpset
import copy
import networkx  as nx
from threading import Lock


#SLEEP_PERIOD = 10
SLEEP_PERIOD = 200

IS_UPDATE = True

class Network_Aware(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _NAME = 'network_aware'

    def __init__(self, *args, **kwargs):
        super(Network_Aware, self).__init__(*args, **kwargs)
        self.name = "Network_Aware"
        self.topology_api_app = self
        self.link_list = []

        # links   :(src_dpid,dst_dpid)->(src_port,dst_port)
        self.link_to_port = {}

        # {(sw,port) :[host1_ip,host2_ip,host3_ip,host4_ip]}
        self.access_table = {}

        # ports
        self.switch_port_table = {}  # dpid->port_num

        # dpid->port_num (ports without link)
        self.access_ports = {}

        # dpid->port_num(ports with contain link `s port)
        self.interior_ports = {}
        self.graph = {}
		
	#self.active_links = []
	self.G = nx.DiGraph()
	#self.G = nx.Graph()
        self.links = []
   
        self.pre_link_to_port = {}
        self.pre_graph = {}
        self.pre_access_table = {}
       
        self.TOPO_LOCK = Lock()
             
        self.monitor_thread = hub.spawn(self._monitor)

    # show topo ,and get topo again
    def _monitor(self):
        i = 0
        while True:

            #	self.show_topology()
            	if i == 5:
                	self.get_topology(None)
                	i = 0
            	hub.sleep(SLEEP_PERIOD)
            	i = i + 1

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        msg = ev.msg
        self.logger.info("switch:%s connected", datapath.id)

        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

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

    def get_switches(self):
        return self.switches

    def get_links(self):
        return self.link_to_port

    # get Adjacency matrix from link_to_port
    def get_graph(self, link_list):
        for src in self.switches:
            for dst in self.switches:
                self.graph.setdefault(src, {dst: float('inf')})
                if src == dst:
                    self.graph[src][src] = 0
                elif (src, dst) in link_list:
                    self.graph[src][dst] = 1
                else:
                    self.graph[src][dst] = float('inf')
        return self.graph


    def create_port_map(self, switch_list):
        for sw in switch_list:
            dpid = sw.dp.id
            self.switch_port_table.setdefault(dpid, set())
            self.interior_ports.setdefault(dpid, set())
            self.access_ports.setdefault(dpid, set())

            for p in sw.ports:
                self.switch_port_table[dpid].add(p.port_no)

    # get links`srouce port to dst port  from link_list,
    # link_to_port:(src_dpid,dst_dpid)->(src_port,dst_port)
    def create_interior_links(self, link_list):
        for link in link_list:
            src = link.src
            dst = link.dst
            self.link_to_port[
                (src.dpid, dst.dpid)] = (src.port_no, dst.port_no)

            # find the access ports and interiorior ports
            if link.src.dpid in self.switches:
                self.interior_ports[link.src.dpid].add(link.src.port_no)
            if link.dst.dpid in self.switches:
                self.interior_ports[link.dst.dpid].add(link.dst.port_no)

    # get ports without link into access_ports
    def create_access_ports(self):
        for sw in self.switch_port_table:
            self.access_ports[sw] = self.switch_port_table[sw] - self.interior_ports[sw]


    def clearAllFlowsAndGroups(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        #clear all flows
        match = parser.OFPMatch()
        self.del_flow(datapath , ofproto.OFPTT_ALL, 0, match, inst=[])
        #clear all groups
        #buckets = []
        #self.del_group(datapath, ofproto.OFPGT_INDIRECT, ofproto.OFPG_ALL, buckets)


    def del_group(self, datapath, type, group_id, buckets):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_DELETE,
                                 type, group_id, buckets)
        datapath.send_msg(req)


    def del_flow(self, datapath , table_id, priority , match , inst):
       ofproto = datapath.ofproto
       parser = datapath.ofproto_parser
       mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE, table_id=table_id, priority=priority,
                                   out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                               match=match , instructions=inst)
       datapath.send_msg(mod)


    def find_failed_link(self, port_no, dpid):
	    #links = get_link(self.topology_api_app, None)
	    for l in self.links:
		if (l.src.dpid == dpid and l.src.port_no == port_no) or (l.dst.dpid == dpid and l.src.port_no == port_no):
					removed_link = l
					return l
	    return None
		
   # def update_topology(self, links):
   #		self.G = nx.DiGraph()
   #             for l in links:
   #			src = l.src
   #			dst = l.dst
   #
   #			self.G.add_edge(src.dpid, dst.dpid, link=l)
    #            print(self.G.edges())

   ### instead of this, we will use the Link Delete event
   # @set_ev_cls(dpset.EventPortModify, MAIN_DISPATCHER)    
   # def port_modify_handler(self, ev):
   #     self.TOPO_LOCK  = True
   #     dp = ev.dp
   #     port_attr = ev.port
        
   #     if port_attr.state == 1:
        	
   #     	self.clearAllFlowsAndGroups(dp) ## or only delete the related flows
   #             self.get_topology(ev)
        #	tmp_list = []
    	#	removed_link = self.find_failed_link(port_attr.port_no, dp.id)
    #	        links = get_link(self.topology_api_app, None)
    #		for l in links:
    #			if (l.src.dpid == dp.id and l.src.port_no == port_attr.port_no) or (l.dst.dpid == dp.id and l.src.port_no == port_attr.port_no):
    #				continue
    #			else: 
    #				tmp_list.append(l)
					

            			
         
     #       	print "\t Considering the removed Link " + str(removed_link)
     #       	if removed_link is not None:
     #			self.update_topology(tmp_list) 
     #			self.clearAllFlowsAndGroups(dp) ## or only delete the related flows
                        
                	#shortest_path_hubs, shortest_path_node = self.topo_shape.find_shortest_path(removed_link.src.dpid)
     #                   print("New shortest path will be  calculated...\n")

        #self.topo_shape.lock.release()
        
     #   self.TOPO_LOCK = False

    @handler.set_ev_cls(event.EventLinkAdd)
    def link_add_handler(self, ev):
        self.logger.info("Link Added: "+ str(ev))
        link = ev.link
        src = link.src
        dst = link.dst
       
        self.G.add_edge(src.dpid, dst.dpid, port=src.port_no, link=link)




    events = [event.EventSwitchEnter,
              event.EventSwitchLeave, event.EventPortAdd,
              event.EventPortDelete, #event.EventPortModify,
              event.EventLinkAdd, event.EventLinkDelete]



    @set_ev_cls(events)
    def get_topology(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        
        self.create_port_map(switch_list)
        self.switches = self.switch_port_table.keys()
        links = get_link(self.topology_api_app, None)
        self.links = links
        #print("\nLinks are : %d\n", len(links))
        self.create_interior_links(links)
        self.create_access_ports()
       
        self.get_graph(self.link_to_port.keys())

		

     # show topo
    def show_topology(self):
        switch_num = len(self.graph)
        if self.pre_graph != self.graph or IS_UPDATE:
            print "---------------------Topo Link---------------------"
            print '%10s' % ("switch"),
            for i in xrange(1, switch_num + 1):
                print '%10d' % i,
            print ""
            for i in self.graph.keys():
                print '%10d' % i,
                for j in self.graph[i].values():
                    print '%10.0f' % j,
                print ""
            self.pre_graph = self.graph
        # show link
        if self.pre_link_to_port != self.link_to_port or IS_UPDATE:
            print "---------------------Link Port---------------------"
            print '%10s' % ("switch"),
            for i in xrange(1, switch_num + 1):
                print '%10d' % i,
            print ""
            for i in xrange(1, switch_num + 1):
                print '%10d' % i,
                for j in xrange(1, switch_num + 1):
                    if (i, j) in self.link_to_port.keys():
                        print '%10s' % str(self.link_to_port[(i, j)]),
                    else:
                        print '%10s' % "No-link",
                print ""
            self.pre_link_to_port = self.link_to_port

        # each dp access host
        # {(sw,port) :[host1_ip,host2_ip,host3_ip,host4_ip]}
        if self.pre_access_table != self.access_table or IS_UPDATE:
            print "----------------Access Host-------------------"
            print '%10s' % ("switch"), '%12s' % "Host"
            if not self.access_table.keys():
                print "    NO found host"
            else:
                for tup in self.access_table:
                    print '%10d:    ' % tup[0], self.access_table[tup]
            self.pre_access_table = self.access_table

    
