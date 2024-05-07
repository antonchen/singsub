#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>
import json

def sing_box_to_clash_node(node_list):
    """Sing-box node to Clash node"""
    """Only support vless node"""
    if node_list[0]['type'] != 'vless':
        return 'Only support vless node'
    clash_nodes = 'proxies:\n'
    for node in node_list:
        clash_node = {
            'type': node['type'],
            'name': node['tag'],
            'server': node['server'],
            'port': node['server_port'],
            'uuid': node['uuid'],
            'flow': node['flow'],
            'servername': node['tls']['server_name'],
            'tls': node['tls']['enabled'],
            'packet-encoding': node['packet_encoding'],
            'udp': True,
            'skip-cert-verify': False
            
        }
        clash_nodes += '- ' + json.dumps(clash_node) + '\n'
    return clash_nodes