#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>
import os
import sys

# 排除关键字
EXCLUDE = '到期|剩余|流量|时间|官网|产品|过期|公告|回国|星链'

CACHE_DIR = os.path.dirname(os.path.abspath(sys.argv[0])) + '/cache/'
CACHE_EXPIRE = 28800