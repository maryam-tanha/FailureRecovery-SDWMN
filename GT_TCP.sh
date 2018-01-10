#!/bin/bash

#PMR1
curl -X POST -d '{
      "dpid": 1,
      "type": "FF",
      "group_id": 10,
      "buckets": [
           
           {  
              "watch_port": 1,
              "actions": [
            {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value":"04:f0:21:11:3d:84"
           },
          {
            "type":"SET_FIELD",
           "field": "eth_dst",
            "value":"04:f0:21:11:3d:82"
           },
           {
               "type": "OUTPUT",
               "port":1 
                  }
             ]
          } ,

          {     
           "watch_port": 2,
           "actions": [
            
           {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value":"04:f0:21:11:3d:78"
          },
         {
             "type":"SET_FIELD",
             "field": "eth_dst",
             "value": "04:f0:21:11:3d:81"
           },

           {   "type": "OUTPUT",
               "port": 2
                  }
             ]
       }

      ]
   }' http://192.168.0.111:8080/stats/groupentry/add


curl -X POST -d '{
    "dpid": 1,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":4,
        "eth_type":2048,
        "ipv4_src":"192.168.0.179",
        "ipv4_dst":"192.168.0.178",
        "tcp_dst":5001,
        "ip_proto":6
    },

    "actions":[

        {
            "type":"GROUP",
            "group_id": 10
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

curl -X POST -d '{
    "dpid": 1,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":4,
        "eth_type":2048,
        "ipv4_src":"192.168.0.179",
        "ipv4_dst":"192.168.0.178",
        "tcp_src":5001,
        "ip_proto":6
    },

     "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:84"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:82"
        },
        {
            "type":"OUTPUT",
            "port": 1
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

curl -X POST -d '{
    "dpid": 1,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":1,
        "eth_type":2048,
        "ipv4_src":"192.168.0.178",
        "ipv4_dst":"192.168.0.179",
        "tcp_src":5001,
        "ip_proto":6
    },
    "actions":[
        {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "00:0d:b9:33:e9:2c"
        },
        {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "00:1d:09:af:ea:2b"
        },
        {
            "type":"OUTPUT",
            "port": 4
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

####################################################
### Primary Path 
####################################################

#PMR2
curl -X POST -d '{
    "dpid": 2,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":1,
        "eth_type":2048,
        "ipv4_src":"192.168.0.179",
        "ipv4_dst":"192.168.0.178",
        "tcp_dst":5001,
        "ip_proto":6
    },
    "actions":[
        {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:83"
        },
        {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:7e"
        },
        {
            "type":"OUTPUT",
            "port": 2
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

curl -X POST -d '{
    "dpid": 2,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":2,
        "eth_type":2048,
        "ipv4_src":"192.168.0.178",
        "ipv4_dst":"192.168.0.179",
        "tcp_src":5001,
        "ip_proto":6
    },
    "actions":[
        {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:82"
        },
        {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:84"
        },
        {
            "type":"OUTPUT",
            "port": 1
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add
 

#PMR5
curl -X POST -d '{
    "dpid": 5,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":2,
        "eth_type":2048,
        "ipv4_src":"192.168.0.179",
        "ipv4_dst":"192.168.0.178",
        "tcp_dst":5001,
        "ip_proto":6
    },
    "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "c8:3a:35:c9:64:f3"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:89"
        },
        {
            "type":"OUTPUT",
            "port": 3
        }

    ]
 }' http://192.168.0.111:8080/stats/flowentry/add
 
curl -X POST -d '{
    "dpid": 5,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":3,
        "eth_type":2048,
        "ipv4_src":"192.168.0.178",
        "ipv4_dst":"192.168.0.179",
        "tcp_src":5001,
        "ip_proto":6
    },
    "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:7e"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:83"
        },
        {
            "type":"OUTPUT",
            "port": 2
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add


#PMR8

curl -X POST -d '{
    "dpid": 8,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":1,
        "eth_type":2048,
        "ipv4_src":"192.168.0.179",
        "ipv4_dst":"192.168.0.178",
        "tcp_dst":5001,
        "ip_proto":6
    },
    "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "00:0d:b9:33:e9:20"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "f0:4d:a2:7b:18:2b"
        },
        {
            "type":"OUTPUT",
            "port": 4
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

curl -X POST -d '{
    "dpid": 8,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":4,
        "eth_type":2048,
        "ipv4_src":"192.168.0.178",
        "ipv4_dst":"192.168.0.179",
        "tcp_src":5001,
        "ip_proto":6
    },
    "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:89"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "c8:3a:35:c9:64:f3"
        },
        {
            "type":"OUTPUT",
            "port": 1
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

####################################################
### Secondary Path 
####################################################

#PMR4
curl -X POST -d '{
    "dpid": 4,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":1,
        "eth_type":2048,
        "ipv4_src":"192.168.0.179",
        "ipv4_dst":"192.168.0.178",
        "tcp_dst":5001,
        "ip_proto":6
    },
    "actions":[
        {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:7d"
        },
        {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:73"
        },
        {
            "type":"OUTPUT",
            "port": 2
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

 curl -X POST -d '{
    "dpid": 4,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":2,
        "eth_type":2048,
        "ipv4_dst":"192.168.0.179",
        "ipv4_src":"192.168.0.178",
        "tcp_src":5001,
        "ip_proto":6
    },
    "actions":[
        {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:81"
        },
        {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:78"
        },
        {
            "type":"OUTPUT",
            "port": 1
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add
 
# PMR7
curl -X POST -d '{
    "dpid": 7,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":2,
        "eth_type":2048,
        "ipv4_src":"192.168.0.179",
        "ipv4_dst":"192.168.0.178",
        "tcp_dst":5001,
        "ip_proto":6
    },
    "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "c8:3a:35:c9:66:e2"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:87"
        },
        {
            "type":"OUTPUT",
            "port": 4
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add
 
 curl -X POST -d '{
    "dpid": 7,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":3,
        "eth_type":2048,
        "ipv4_dst":"192.168.0.179",
        "ipv4_src":"192.168.0.178",
        "tcp_src":5001,
        "ip_proto":6
    },
    "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:73"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "04:f0:21:11:3d:7d"
        },
        {
            "type":"OUTPUT",
            "port": 2
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

# PMR8
curl -X POST -d '{
    "dpid": 8,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":2,
        "eth_type":2048,
        "ipv4_src":"192.168.0.179",
        "ipv4_dst":"192.168.0.178",
        "tcp_dst":5001,
        "ip_proto":6
    },
    "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "00:0d:b9:33:e9:20"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "f0:4d:a2:7b:18:2b"
        },
        {
            "type":"OUTPUT",
            "port": 4
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add

curl -X POST -d '{
    "dpid": 8,
    "cookie": 1,
    "cookie_mask": 1,
    "table_id": 0,
    "idle_timeout": 3000,
    "hard_timeout": 65000,
    "priority": 11111,
    "flags": 1,
    "match":{
        "in_port":4,
        "eth_type":2048,
        "ipv4_dst":"192.168.0.179",
        "ipv4_src":"192.168.0.178",
        "tcp_src":5001,
        "ip_proto":6
    },

   "actions":[
         {
            "type":"SET_FIELD",
            "field": "eth_src",
            "value": "04:f0:21:11:3d:89"
        },
         {
            "type":"SET_FIELD",
            "field": "eth_dst",
            "value": "c8:3a:35:c9:64:f3"
        },
        {
            "type":"OUTPUT",
            "port": 1
        }
    ]
 }' http://192.168.0.111:8080/stats/flowentry/add
