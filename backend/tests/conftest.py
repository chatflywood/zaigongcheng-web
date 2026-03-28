# -*- coding: utf-8 -*-
"""
pytest 配置文件
"""
import os
import sys

# 禁用代理环境变量
for key in ['all_proxy', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(key, None)
