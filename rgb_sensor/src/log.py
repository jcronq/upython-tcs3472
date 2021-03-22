# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 17:12:42 2019

@author: jcron
"""

import urequests


def info(msg):
    data = { "type": "info", "msg": msg }
    headers= {'Content-Type': 'application/json', 'Accept': 'text/plain'}
    response = urequests.post("http://192.168.1.105:5000/log", json=data, headers=headers )
    response.close()