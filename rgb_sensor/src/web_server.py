# -*- coding: utf-8 -*-
"""
Created on Sun Nov  3 15:00:47 2019

@author: jcron
"""

import usocket
import ujson
import _thread
import machine

class WebServer:

    _run = True
    addr = ('', 8008)

    def __init__(self, sensor):
        self.sensor = sensor
        self.socket= usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        addr = usocket.getaddrinfo('0.0.0.0', 8008)[0][-1]
        print(addr, type(addr))
        self.socket.bind(addr)

    def start(self):
        _thread.start_new_thread(self.run, ())
        
    def parseHeader(self, header):
        pop0 = str(header.pop(0))[2:-5]
        print('pop0',pop0)
        stripped = pop0.strip()
        print('stripped', stripped)
        target = stripped.split(' ')
        print(target)
        method = target[0]
        uri = target[1]
        version = target[2]
        
        result = {
                'Method': method,
                'URI': uri,
                'Version': version, 
            }
        
        for option in header:
            parts = str(option)[2:-5].split(': ')
            print(parts)
            result[parts[0]] = parts[1]

        return result            
        
    def run(self):
        self.socket.listen(5)
        while self._run:
            conn, addr = self.socket.accept()
            try:
                print('client conneted from', addr)
                recv_file = conn.makefile('rwb', 0)
                header_lines = []
                while True:
                    line = recv_file.readline()
                    if not line or line == b'\r\n':
                        break
                    else:
                        header_lines.append(line)
                
                header = self.parseHeader(header_lines)
                
                if header['Method' ] == 'POST':
                    if header['URI'] == '/reset':
                        conn.send("HTTP/1.1 200 RESETING\n")
                        conn.close()
                        machine.reset()
                    else:
                        raise Exception("Invalid URI: {}".format(header['URI']))
                elif header['Method'] == 'GET':
                    if header['URI'] == '/rgbcct/latest':
                        dataObj = self.sensor.getRGBCCtLatest()
                        conn.send(ujson.dumps(dataObj))
                elif header['Method'] == 'PUT':
                    fileName = header['URI']
                    file = open(fileName, 'w')
                    
                    contentLength = int(header['Content-Length'])
                    while contentLength > 0:
                        getsize = 1024
                        if contentLength < getsize:
                            getsize = contentLength
                        data = conn.recv(getsize)
    
                        file.write(data)
                        contentLength -= getsize
                    file.close()
                else:
                    raise Exception("Only accepting PUT requests")
                
                
                conn.send("HTTP/1.1 201 Created\n")
            except:
                print('500')
                conn.send("HTTP/1.1 500 Not OK\n")
                
            finally:
                conn.close()
            
            