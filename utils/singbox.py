#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>
import re
import json
import os
import sys
from utils.tool import regex_patterns, is_ip

def read_template(version='1.8'):
    """读取模板"""
    with open(os.path.dirname(os.path.abspath(sys.argv[0])) + '/templates/' + str(version) + '-config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def match_keywords(filter, nodes):
    """根据关键字筛选节点"""
    temp = []
    flag = False
    if filter['action'] == 'exclude':
        flag = True

    keywords = re.sub(r'\|\|', '|', '|'.join(filter['keywords']))
    if not keywords:
        return [node['tag'] for node in nodes]
    
    pattern = re.compile(keywords)
    for node in nodes:
        match_flag = bool(pattern.search(node['tag']))
        if match_flag ^ flag:
            temp.append(node['tag'])
    return temp

def apply_filter(node_list, group_template):
    """根据过滤条件筛选节点"""
    outbounds = []
    if 'filter' in group_template:
        for filter in group_template['filter']:
            outbounds.extend(match_keywords(filter, node_list))
    else:
        outbounds = [node['tag'] for node in node_list]
    return outbounds

def set_relay_out(relay_outs):
    """设置落地出口"""
    for node in relay_outs:
        # 删除 tag 中，-SS -SSR -V2 -V2ray -Vmess -Trojan 关键字
        node['tag'] = '[Relay]' + re.sub(r'(-SS|-SSR|-VLESS|-VMess|-Trojan)$', '', node['tag'])
        # 判断节点国家
        for country, pattern in regex_patterns.items():
            if pattern.search(node['tag']):
                node['detour'] = country
                break
    return relay_outs

def get_node_name(nodes):
    """获取节点名称"""
    node_names = []
    for node in nodes:
        node_names.append(node['tag'])
    return node_names

def get_node_domain(nodes):
    """获取节点域名 """
    node_domains = []
    for node in nodes:
        node_domains.append(node['server'])

    return list(set(node_domains))

def generate_sing_box_config(nodes,version,relay_outs=None):
    """生成 sing-box 配置"""
    template = read_template(version)
    config = {}
    config['log'] = template['log']
    config['experimental'] = template['experimental']
    config['dns'] = template['dns']
    config['inbounds'] = template['inbounds']
    config['outbounds'] = []
    auto_tags = []
    for t_ob in template["outbounds"]:
        if t_ob.get("outbounds"):
            temp_group = t_ob
            if '{all}' in t_ob["outbounds"]:
                if 'filter' in t_ob:
                    group = apply_filter(nodes, t_ob)
                    mark_index = temp_group["outbounds"].index('{all}')
                    temp_group["outbounds"].pop(mark_index)
                    temp_group["outbounds"][mark_index:mark_index] = group
                    # 删除 filter
                    temp_group.pop('filter')
                else:
                    mark_index = temp_group["outbounds"].index('{all}')
                    temp_group["outbounds"].pop(mark_index)
                    temp_group["outbounds"][mark_index:mark_index] = [node['tag'] for node in nodes]
                # 如果节点组为空，则不添加
                if temp_group["outbounds"]:
                    config['outbounds'].append(temp_group)
                    if temp_group.get("tag") != "Manual" or temp_group.get("tag", None) == None:
                        auto_tags.append(temp_group["tag"])
            else:
                config['outbounds'].append(t_ob)
        else:
            config['outbounds'].append(t_ob)
    for ob in config['outbounds']:
        if ob.get('tag') == 'Auto':
            auto_tags.append('direct')
            ob['outbounds'] = auto_tags
        if ob.get('tag') == 'OpenAI':
            auto_tags.remove('direct')
            ob['outbounds'] = auto_tags

    if relay_outs:
        relay_outs_node = set_relay_out(relay_outs)
        for ob in config['outbounds']:
            if ob.get('outbounds'):
                if '{relay_outs}' in ob['outbounds']:
                    mark_index = ob["outbounds"].index('{relay_outs}')
                    ob["outbounds"].pop(mark_index)
                    ob["outbounds"][mark_index:mark_index] = get_node_name(relay_outs_node)

        config['outbounds'].extend(relay_outs_node)
    else:
        for ob in config['outbounds']:
            if ob.get('outbounds'):
                if '{relay_outs}' in ob['outbounds']:
                    ob['outbounds'].remove('{relay_outs}')

    # 添加节点
    config['outbounds'].extend(nodes)
    for rule in config['dns']['rules']:
        if rule.get('domain'):
            if 'ghproxy.com' in rule['domain']:
                rule['domain'].extend([server for server in get_node_domain(nodes) if is_ip(server) == False])
                if relay_outs:
                    rule['domain'].extend([server for server in get_node_domain(relay_outs) if is_ip(server) == False])
    config['route'] = template['route']
    return config