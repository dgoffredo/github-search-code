#!/usr/bin/env python3

import json
import os
import requests
import urllib.parse


url = 'https://api.github.com/search/code?' + urllib.parse.urlencode({
    'q': 'ngx_module_order',
    'per_page': 1,
    'access_token': os.environ['access_token'],
    'page': 1
})
print(url)

response = requests.get(url)
print(response.json())
