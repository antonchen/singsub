#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>

import asyncio
import json
from flask import Flask, request
from utils.singbox import generate_sing_box_config
from utils.tool import cached_multi_threaded_get
from utils.parsers import parse_subscribe

# 解析订阅链接
# 传入 urls dict
# 返回节点列表
def parse_subscribe_url(urls):
    # 初始化节点列表
    nodes = []
    # 获取订阅内容
    subscribe_data = asyncio.run(cached_multi_threaded_get(urls))
    # 解析订阅内容
    for content in subscribe_data:
        if content is not None:
            nodes.extend(parse_subscribe(content))
    # 返回节点列表
    return nodes

# Flask 提供 API 接口，用于转换订阅格式为 sing-box 配置
app = Flask(__name__)

# 接受 POST 请求，请求数据为 JSON 格式
@app.route('/api/v1/sing-box', methods=['POST'])
def sing_box():
    if request.method == 'POST':
        # 获取 POST 数据
        data = request.get_json()
        if 'version' in data:
            version = data['version']
        else:
            version = '1.8'
        # 解析订阅链接
        node_list = parse_subscribe_url(data['urls'])
        # 如 node_list 为空，返回 500
        if not node_list:
            return 'Internal Server Error', 500
        # 判断是否有中继节点
        if 'relay_outs' in data:
            # 解析中继节点
            relay_outs = parse_subscribe_url([data['relay_outs']])
            # 生成 sing-box 配置
            sing_box = generate_sing_box_config(node_list, version=version, relay_outs=relay_outs)
        else:
             sing_box = generate_sing_box_config(node_list, version=version)
        # 返回 sing-box 配置
        return json.dumps(sing_box, ensure_ascii=False)
    else:
        return 'Method Not Allowed'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)