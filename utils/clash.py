#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>
import json

def generate_clash_node(node_list):
    """转换订阅为 Clash 节点格式"""
    """Support ss or vless node"""
    if node_list[0]['type'] != 'vless' and node_list[0]['type'] != 'shadowsocks' and node_list[0]['type'] != 'vmess':
        print(node_list[0]['type'])
        return 'Support ss/vless/vmess node'
    clash_nodes = 'proxies:\n'
    for node in node_list:
        if node['type'] == 'vmess':
            clash_node = {
                'type': 'vmess',
                'name': node['tag'],
                'server': node['server'],
                'port': node['server_port'],
                'uuid': node['uuid'],
                'alterId': node['alter_id'],
                'cipher': node['security'],
                'udp': True
            }
            if node.get('tls',{}).get('enabled',False):
                clash_node['tls'] = node['tls']['enabled']
                clash_node['skip-cert-verify'] = False
                if node['tls']['server_name']:
                    clash_node['servername'] = node['tls']['server_name']
            if node.get('transport',{}).get('type',False):
                clash_node['network'] = node['transport']['type']
                if node['transport']['type'] == 'ws':
                    clash_node['ws-opts'] = {}
                    clash_node['ws-opts']['path'] = node['transport']['path']
                    if node.get('transport',{}).get('headers',{}).get('Host',False):
                        clash_node['ws-opts']['headers'] = {'Host': node['transport']['headers']['Host']}
                elif node['transport']['type'] == 'grpc':
                    clash_node['grpc-opts'] = {}
                    clash_node['grpc-opts']['grpc-service-name'] = node['transport']['service-name']
                elif node['transport']['type'] == 'h2':
                    clash_node['h2-opts'] = {}
                    clash_node['h2-opts']['path'] = node['transport']['path']
                    clash_node['h2-opts']['host'] = node['transport']['headers']['Host']

        elif node['type'] == 'vless':
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