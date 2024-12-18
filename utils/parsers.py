#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>
import base64
import re
import json
import utils.config as config
from urllib.parse import urlparse, parse_qs, unquote

# base64 解码
def b64decode(str):
    missing_padding = 4 - len(str) % 4
    if missing_padding:
        str += '=' * missing_padding
    return base64.urlsafe_b64decode(str).decode('utf-8')

# 删除 emoji
def remove_emoji(str):
    try:
        # UCS-4
        highpoints = re.compile(u'[\U00010000-\U0010ffff]')
    except re.error:
        # UCS-2
        highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    # control
    control = re.compile(u'[\x00-\x1F\x7F-\x9F]')
    return control.sub('', highpoints.sub('', str))

# 删除空行、\r
def noblank_line(str):
    return re.sub(r'\r', '', re.sub(r'\n\n', '\n', str))

# 删除空格、*
def nospace(str):
    return re.sub(r'\s|\*', '', str)

# 生成 ss 节点
# {
#   "type": "shadowsocks",
#   "tag": "ss-out",

#   "server": "127.0.0.1",
#   "server_port": 1080,
#   "method": "2022-blake3-aes-128-gcm",
#   "password": "8JCsPssfgS8tiRwiMlhARg==",
#   "plugin": "",
#   "plugin_opts": "",
#   "network": "udp",
#   "udp_over_tcp": false | {},
#   "multiplex": {},

#   ... // 拨号字段
# }
def ss(parsed_url):
    node = {}
    node['type'] = 'shadowsocks'
    node['tag'] = nospace(remove_emoji(unquote(parsed_url.fragment)))
    url = urlparse("ss://" + b64decode(parsed_url.netloc))
    node['server'] = url.hostname
    node['server_port'] = url.port
    node['password'] = url.password
    node['method'] = url.username
    params = parse_qs(parsed_url.query)
    if 'plugin' in params:
        node['plugin'] = params['plugin'][0].split(';')[0]
        node['plugin_opts'] = re.sub(r'^.*?;', '', params['plugin'][0])
    # node['udp_over_tcp'] = { "enabled": True, "version": 2 }
    return node

# 生成 ssr 节点
def ssr(parsed_url):
    node = {}
    params_dict = {'obfsparam':'obfs_param','protoparam':'protocol_param','remarks':'tag'}
    node['type'] = 'shadowsocksr'
    url = b64decode(parsed_url.netloc)
    parts = url.split('/?')[0].split(':')
    node['server'] = parts[0]
    node['server_port'] = int(parts[1])
    node['protocol'] = parts[2]
    node['method'] = parts[3]
    node['obfs'] = parts[4]
    node['password'] = b64decode(parts[5])
    params = url.split('/?')[1]
    params = parse_qs(params)
    
    for key in params:
        if key in params_dict.keys():
            if key == 'remarks':
                node[params_dict[key]] = nospace(remove_emoji(unquote(params[key][0])))
            else:
                node[params_dict[key]] = params[key][0]
            
    return node

# 生成 vmess 节点
# {
#     "tag": "🇺🇸 奈飞  tiktok专线04",
#     "type": "trojan",
#     "server": "y31.huamaoyun.live",
#     "server_port": 2087,
#     "password": "1faaefc9-0ddd-48d6-ba03-45bd3c9a8ad5",
#     "tls": {
#     "enabled": true,
#     "insecure": true,
#     "server_name": "a609.huamaoyun.live"
#     },
#     "transport": {
#     "type": "grpc",
#     "service_name": "n"
#     }
# }
    
def vmess(url):
    node = {}
    vmess_info = json.loads(b64decode(url.split('vmess://')[1]))
    node['type'] = 'vmess'
    node['tag'] = nospace(remove_emoji(vmess_info['ps']))
    node['server'] = vmess_info['add']
    node['server_port'] = int(vmess_info['port'])
    node['uuid'] = vmess_info['id']
    node['alter_id'] = int(vmess_info.get('aid','0'))
    node['packet_encoding'] = 'xudp'
    if vmess_info.get('scy'):
        if vmess_info['scy'] != 'http' or vmess_info['scy'] != 'gun':
            node['network'] = 'auto'
        else:
            node['network'] = vmess_info['scy']
    if vmess_info.get('tls') and vmess_info['tls'] != '' and vmess_info['tls'] != 'none':
        node['tls'] = {
            'enabled': True,
            'insecure': True,
            'server_name': vmess_info.get('host', '') if vmess_info.get("net") not in ['h2', 'http'] else ''
        }
        if vmess_info.get('sni'):
            node['tls']['server_name'] = vmess_info['sni'][0]
        if vmess_info.get('fp'):
            node['tls']['utls'] = {
                'enabled': True,
                'fingerprint': vmess_info['fp'][0]
            }
    if vmess_info['net'] in ['h2', 'http']:
        node['network'] = 'h2'
        node['h2-path'] = vmess_info['path']
        node['h2-host'] = vmess_info['host']
    elif vmess_info['net'] == 'ws':
        node['transport'] = {
            'type': 'ws'
        }
        if vmess_info.get('host'):
            node['transport']['Headers'] = {
                'Host': vmess_info['host']
            }
        if vmess_info.get('path'):
            node['transport']['path'] = vmess_info['path'].rsplit('?')[0]
        if '?ed=' in vmess_info.get('path', ''):
            node['transport']['early_data_header_name'] = 'Sec-WebSocket-Protocol'
            node['transport']['max_early_data'] = int(re.search(r'\d+', vmess_info.get('path').rsplit("?ed=")[1]).group())  
    elif vmess_info['net'] == 'quic':
        node['transport'] = {
            'type':'quic'
        }
    elif vmess_info['net'] == 'grpc':
        node['transport'] = {
            'type':'grpc',
            'service_name':vmess_info.get('path', '')
        }
    if vmess_info.get('protocol'):
        node['multiplex'] = {
            'enabled': True,
            'protocol': vmess_info['protocol'],
            'max_streams': int(vmess_info.get('max_streams', '0'))
        }
        if vmess_info.get('max_connections'):
            node['multiplex']['max_connections'] = int(vmess_info['max_connections'])
        if vmess_info.get('min_streams'):
            node['multiplex']['min_streams'] = int(vmess_info['min_streams'])
        if vmess_info.get('padding') == 'True':
            node['multiplex']['padding'] = True
    return node

# 生成 vless 节点
# {
#     "tag": "🇺🇸 美西4K2",
#     "type": "vless",
#     "server": "f2.huamaoyun.live",
#     "server_port": 8080,
#     "uuid": "1faaefc9-0ddd-48d6-ba03-45bd3c9a8ad5",
#     "packet_encoding": "xudp",
#     "transport": {
#     "type": "ws",
#     "path": "/",
#     "headers": {
#         "Host": "a602.huamaoyun.live"
#     },
#     "early_data_header_name": "Sec-WebSocket-Protocol",
#     "max_early_data": 2048
#     }
# },
def vless(parsed_url):
    node = {}
    node['type'] = 'vless'
    node['tag'] = remove_emoji(nospace(unquote(parsed_url.fragment)))
    node['server'] = parsed_url.hostname
    node['server_port'] = parsed_url.port
    node['uuid'] = parsed_url.username
    params = parse_qs(parsed_url.query)
    node['packet_encoding'] = params.get('packetEncoding', 'xudp')
    if params.get('flow'):
        node['flow'] = 'xtls-rprx-vision'
    if params.get('security', '') not in ['None', 'none', '']:
        node['tls'] = {
            'enabled': True,
            'insecure': True,
            'server_name': ''
        }
        if params.get('allowInsecure') == '0':
            node['tls']['insecure'] = False
        node['tls']['server_name'] = params.get('sni', '')[0] or params.get('peer', '')[0]
        if params.get('fp'):
            node['tls']['utls'] = {
                'enabled': True,
                'fingerprint': params['fp'][0]
            }
        if params['security'] == 'reality':
            node['tls']['reality'] = {
                'enabled': True,
                'public_key': params.get('pbk'),
            }
            if params.get('sid'):
                node['tls']['reality']['short_id'] = params['sid']
            node['tls']['utls'] = {
                'enabled': True,
                'fingerprint': 'chrome'
            }
    if params.get('type'):
        if params['type'] == 'http':
            node['transport'] = {
                'type':'http'
            }
        if params['type'] == 'ws':
            node['transport'] = {
                'type':'ws',
                "path": params.get('path', '').rsplit("?")[0],
                "headers": {
                    "Host": '' if params.get('host') is None and params.get('sni') == 'None' else params.get('host', params.get('sni', ''))
                }
            }
            if node.get('tls'):
                if node['tls']['server_name'] == '':
                    if node['transport']['headers']['Host']:
                        node['tls']['server_name'] = node['transport']['headers']['Host']
            if '?ed=' in params.get('path', ''):
                node['transport']['early_data_header_name'] = 'Sec-WebSocket-Protocol'
                node['transport']['max_early_data'] = int(re.search(r'\d+', params.get('path').rsplit("?ed=")[1]).group())
        if params['type'] == 'grpc':
            node['transport'] = {
                'type':'grpc',
                'service_name':params.get('path', '')
            }
    if params.get('protocol'):
        node['multiplex'] = {
            'enabled': True,
            'protocol': params['protocol'],
            'max_streams': int(params.get('max_streams', '0'))
        }
        if params.get('max_connections'):
            node['multiplex']['max_connections'] = int(params['max_connections'])
        if params.get('min_streams'):
            node['multiplex']['min_streams'] = int(params['min_streams'])
        if params.get('padding') == 'True':
            node['multiplex']['padding'] = True
    
    return node
    
# 生成 trojan 节点
# {
#     "tag": "🇯🇵 日本东京04",
#     "type": "trojan",
#     "server": "y27.huamaoyun.live",
#     "server_port": 2053,
#     "password": "1faaefc9-0ddd-48d6-ba03-45bd3c9a8ad5",
#     "tls": {
#     "enabled": true,
#     "insecure": true,
#     "server_name": "a1031.huamaoyun.live"
#     },
#     "transport": {
#     "type": "grpc",
#     "service_name": "s"
#     }
# }
def trojan(parsed_url):
    node = {}
    node['type'] = 'trojan'
    node['tag'] = remove_emoji(nospace(unquote(parsed_url.fragment)))
    node['server'] = parsed_url.hostname
    node['server_port'] = parsed_url.port
    node['password'] = parsed_url.username
    node['tls'] = {
        'enabled': True,
        'insecure': True
    }
    params = parse_qs(parsed_url.query)
    if params.get('allowInsecure') and params.get('allowInsecure') == '0':
        node['tls']['insecure'] = False
    if params.get('alpn'):
        node['tls']['alpn'] = params.get('alpn').strip('{}').split(',')
    if params.get('sni'):
        node['tls']['server_name'] = params.get('sni', '')[0]
    if params.get('fp'):
        node['tls']['utls'] = {
            'enabled': True,
            'fingerprint': params.get('fp')[0]
        }
    if params.get('type'):
        if params['type'] == 'h2':
            node['transport'] = {
                'type':'http',
                'host':params.get('host', node['server']),
                'path':params.get('path', '/')
            }
        if params['type'] == 'ws':
            if params.get('host'):
                node['transport'] = {
                     'type':'ws',
                     'path':params.get('path', '/'),
                     'headers': {
                         'Host': params.get('host')
                    }
                }
        if params['type'] == 'grpc':
            node['transport'] = {
                'type':'grpc',
                'service_name':params.get('serviceName', '')[0]
            }
    if params.get('protocol'):
        node['multiplex'] = {
            'enabled': True,
            'protocol': params['protocol'],
            'max_streams': int(params.get('max_streams', '0'))
        }
        if params.get('max_connections'):
            node['multiplex']['max_connections'] = int(params['max_connections'])
        if params.get('min_streams'):
            node['multiplex']['min_streams'] = int(params['min_streams'])
        if params.get('padding') == 'True':
            node['multiplex']['padding'] = True
    return node

# 解析订阅节点, 返回 sing-box 节点列表
def parse_subscribe(subscribe):
    # base64 解码, 删除空行、emoji
    subscribe = noblank_line(b64decode(subscribe))
    # 以换行符分割
    node_list_raw = subscribe.split('\n')
    nodes = []
    # 遍历节点
    for url in node_list_raw:
        parsed_url = urlparse(url)
        if parsed_url.scheme == 'ss':
            nodes.append(ss(parsed_url))
        elif parsed_url.scheme == 'ssr':
            nodes.append(ssr(parsed_url))
        elif parsed_url.scheme == 'vmess':
            nodes.append(vmess(url))
        elif parsed_url.scheme == 'vless':
            nodes.append(vless(parsed_url))
        elif parsed_url.scheme == 'trojan':
            nodes.append(trojan(parsed_url))
    # 删除无用节点
    node_list = []
    for node in nodes:
        pattern = re.compile(config.EXCLUDE)
        if pattern.findall(node['tag']):
            pass
        else:
            node_list.append(node)
    return node_list
            