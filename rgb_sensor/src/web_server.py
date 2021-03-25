# -*- coding: utf-8 -*-
"""
Created on Sun Nov  3 15:00:47 2019

@author: jcron
"""

import usocket
import ujson
import _thread

class WebServer:

    _run = True
    addr = ('', 8008)

    def __init__(self, *, enable_web_dav=False):
        self.__router = {
            "POST": {},
            "GET": {},
        }
        self.__socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        addr = usocket.getaddrinfo('0.0.0.0', 8008)[0][-1]
        print(addr, type(addr))
        self.__socket.bind(addr)

    def start_listening(self):
        _thread.start_new_thread(self.__run, ())
    
    def POST(self, path):
        def wrapper(func):
            def inner_call(*args, connection, **kwargs):
                if 'connection' in dir(func):
                    return func(*args, connection=connection, **kwargs)
                else:
                    return func(*args, **kwargs)
            self.__router["POST"][path] = inner_call
            return inner_call
        return wrapper

    def GET(self, path):
        def wrapper(func):
            def inner_call(*args, connection, **kwargs):
                if 'connection' in dir(func):
                    return func(*args, connection=connection, **kwargs)
                else:
                    return func(*args, **kwargs)
            self.__router["GET"][path] = inner_call
            return inner_call
        return wrapper

    def __parse_header(self, header):
        pop0 = str(header.pop(0))[2:-5]
        print('pop0',pop0)
        stripped = pop0.strip()
        print('stripped', stripped)
        method, uri, version = stripped.split(' ')

        result = {
                'Method': method,
                'URI': uri,
                'Version': version, 
            }
        
        print(result)
        
        for option in header:
            parts = str(option)[2:-5].split(': ')
            print(parts)
            result[parts[0]] = parts[1]

        return result
        
    def __run(self):
        self.__socket.listen(5)
        while self._run:
            conn, addr = self.__socket.accept()
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
                
                header = self.__parse_header(header_lines)

                method = header["Method"]
                uri = header["URI"]
                if method in ["PUT", "DELETE"] and not self.__web_dav_enabled: 
                    err_msg = "WEB DAV has not been enabled.  Unable to process {} request.".format(method)
                    print(err_msg)
                    raise RuntimeError(err_msg)
                elif method not in ["GET", "POST", "PUT", "DELETE"]:
                    err_msg = "{} has not been implemented".format(method)
                    print(err_msg)
                    raise NotImplementedError(err_msg)
                else:
                    if header['Method'] == 'PUT' and self.__web_dav_enabled:
                        fileName = uri
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
                        conn.send("HTTP/1.1 201 Created\n")
                    elif header['Method'] == 'DELETE' and self.__web_dav_enabled:
                        fileName = header['URI']
                        if os.path.isdir(path):
                            os.rmdir(path)
                        elif os.path.isfile(path):
                            os.remove(path)
                        conn.send("HTTP/1.1 204 Deleted\n")
                    elif uri in self.__router[method]:
                        callback = self.__router[method][uri]
                        result = callback(connection=conn)
                        if isinstance(result, str):
                            result_str = result
                        else:
                            result_str = ujson.dumps(result)
                        response = "HTTP/1.1 200 OK\r\n\r\n"+result_str
                        print(response)
                        conn.send(response)

                    else:
                        err_msg = "Endpoint not implemented {}:{}".format(method, uri)
                        print(err_msg)
                        raise RuntimeError(err_msg)
                    
            except RuntimeError:
                print('500')
                conn.send("HTTP/1.1 500 Not OK\n")
                
            finally:
                conn.close()
            
            