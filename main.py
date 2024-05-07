#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>

import asyncio
import json
import os
import sys
import shutil
from flask import Flask, request
from utils.singbox import generate_sing_box_config
from utils.tool import cached_multi_threaded_get
from utils.parsers import parse_subscribe
from utils.clash import sing_box_to_clash_node

# 解析订阅链接
# 传入 urls dict
# 返回节点列表
def parse_subscribe_url(urls):
    nodes = []
    subscribe_data = asyncio.run(cached_multi_threaded_get(urls))
    for content in subscribe_data:
        if content is not None:
            nodes.extend(parse_subscribe(content))
    return nodes

# Flask 提供 API 接口，用于转换订阅格式为 sing-box 配置
app = Flask(__name__)

# 接受 POST 和 GET 请求
# POST 请求需要传入 urls 和 relay_outs 参数
# urls 为订阅链接，relay_outs 为转发节点订阅链接
# GET 请求需要传入 urls 参数
@app.route('/api/v1/sing-box', methods=['POST', 'GET'])
def sing_box():
    if request.method == 'POST':
        data = request.get_json()
        if 'config' in data:
            config = data['config']
        else:
            config = 'default'

        node_list = parse_subscribe_url(data['urls'])
        if not node_list:
            return 'Internal Server Error', 500

        if 'relay_outs' in data:
            relay_outs = parse_subscribe(data['relay_outs'])
            sing_box = generate_sing_box_config(node_list, config=config, relay_outs=relay_outs)
        else:
             sing_box = generate_sing_box_config(node_list, config=config)
        return json.dumps(sing_box, ensure_ascii=False)
    elif request.method == 'GET':
        url = request.args.get('url')
        config = request.args.get('config')
        if url is None:
            return 'Bad Request', 400
        else:
            node_list = parse_subscribe_url([url])
            if not node_list:
                return 'Internal Server Error', 500
            if config is not None:
                sing_box = generate_sing_box_config(node_list, config=config)
            else:
                sing_box = generate_sing_box_config(node_list, config='default')
            return json.dumps(sing_box, ensure_ascii=False)
    else:
        return 'Method Not Allowed'

@app.route('/api/v1/clash-node', methods=['POST', 'GET'])
def clash_node():
    urls = []
    if request.method == 'POST':
        data = request.get_json()
        urls.extend(data['urls'])
    elif request.method == 'GET':
        urls.extend(request.args.get('urls').split('|'))
    nodes = parse_subscribe_url(urls)
    return sing_box_to_clash_node(nodes)

if __name__ == '__main__':
    templates_path = os.path.dirname(os.path.abspath(sys.argv[0])) + '/templates'
    default_templates_path = os.path.dirname(os.path.abspath(sys.argv[0])) + '/default_templates'
    if not os.path.exists(templates_path) or not os.listdir(templates_path):
        shutil.copytree(default_templates_path, templates_path, dirs_exist_ok=True)

    app.run(host='0.0.0.0', port=5000)