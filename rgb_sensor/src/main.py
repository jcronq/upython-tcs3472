# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 16:00:35 2019

@author: jcron
"""
from src.rgb_sensor_tcs34725 import Controller
from src.web_server import WebServer

def startWebServer(sensor):
    server = webServer(sensor)
    server.start()

def connect(cb):
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('quantum field', '19930626')
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())
    cb()

def main():    
    # print("hello world")
    sensor = Controller(Controller.INTEGRATIONTIME_154MS, Controller.GAIN_1X)
    # cb = lambda: startWebServer(sensor)
    # connect(cb)