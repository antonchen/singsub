#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>
import json

def generate_clash_node(node_list):
    """转换订阅为 Clash 节点格式"""
    """Support ss or vless node"""
    if node_list[0]['type'] != 'vless' and node_list[0]['type'] != 'shadowsocks':
        print(node_list[0]['type'])
        return 'Support ss or vless node'
    clash_nodes = 'proxies:\n'
    for node in node_list:
        if node['type'] == 'vless':
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
        elif node['type'] == 'shadowsocks':
            clash_node = {
                'type': 'ss',
                'name': node['tag'],
                'server': node['server'],
                'port': node['server_port'],
                'cipher': node['method'],
                'password': node['password'],
                'udp': True,
                'udp-over-tcp': True,
                'udp-over-tcp-version': 2
            }
        clash_nodes += '- ' + json.dumps(clash_node) + '\n'
    return clash_nodes