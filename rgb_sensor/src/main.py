# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 16:00:35 2019

@author: jcron
"""
import machine
from src.rgb_sensor_tcs34725 import Controller
from src.lite_server.web_server import WebServer
from micropython import const

LED_PIN = const(13)
INTERRUPT_PIN = const(23)
SCL_PIN = const(22)
SDA_PIN = const(21)

def start_webserver(sensor):
    server = WebServer(enable_web_dav=True)

    @server.POST("/reset")
    def reset_esp32(response):
        response.set_status(200)
        response.send()
        machine.reset()
    
    @server.GET("/rgbcct")
    def get_rgbcct():
        rgb = sensor.color_raw
        ct = sensor.ct
        lux = sensor.lux
        return [rgb[0], rgb[1], rgb[2], rgb[3], ct, lux]

    @server.GET("/status")
    def get_status():
        status = sensor.status
        return status

    server.start_listening()

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

def run():
    print("hello world")
    sensor = Controller(SCL_PIN, SDA_PIN, 9600, LED_PIN, INTERRUPT_PIN)
    print("sensor initialized")
    cb = lambda: start_webserver(sensor)
    connect(cb)