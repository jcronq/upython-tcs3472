# -*- coding: utf-8 -*-
"""
Created on Sun Nov  3 15:00:47 2019

@author: jcron
"""

import usocket
import ujson
import _thread
from src.lite_server.response import Response
from src.lite_server.request import Request
import src.lite_server.dav_functions as web_dav


def identify_additional_args(method, uri, func, optional_args):
    methods = dir(func)
    additional_args = []
    for arg in optional_args:
        if arg in methods:
            additional_args.append(arg)
    
    return additional_args

def add_additional_args(additional_args, *, optional_args, kwargs):
    for arg in additional_args:
        kwargs[arg] = optional_args[arg]
    return kwargs

def get_inner_func(method, uri, func):
    additional_args = identify_additional_args(method, uri, func, ['request', 'response'])
    def inner_call(*args, request, response, **kwargs):
        kwargs = add_additional_args(additional_args, optional_args={'response': response, 'request': request}, kwargs=kwargs)
        return func(*args, **kwargs)
    return inner_call

class WebServer:
    _run = True
    addr = ('', 8008)

    def __init__(self, *, enable_web_dav=False):
        self.__router = {
            "POST": {},
            "GET": {},
        }
        self.__socket = None

    def start_listening(self):
        self.__socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        addr = usocket.getaddrinfo('0.0.0.0', 8008)[0][-1]
        self.__socket.bind(addr)
        print("listening on {}:{}".format(addr[0], addr[1]))
        _thread.start_new_thread(self.__run, ())
    
    def POST(self, uri):
        def wrapper(func):
            inner_call = get_inner_func('POST', uri, func)
            self.__router["POST"][uri] = inner_call
            return inner_call
        return wrapper

    def GET(self, uri):
        def wrapper(func):
            inner_call = get_inner_func('GET', uri, func)
            self.__router["GET"][uri] = inner_call
            return inner_call
        return wrapper

    def __run(self):
        self.__socket.listen(5)
        while self._run:
            conn, addr = self.__socket.accept()
            try:
                request = Request(conn)
                print('client conneted from', addr)
                method = request.method
                uri = request.uri

                if method in ["PUT", "DELETE"] and not self.__web_dav_enabled: 
                    err_msg = "WEB DAV has not been enabled.  Unable to process {} request.".format(method)
                    print(err_msg)
                    raise RuntimeError(err_msg)
                elif method not in ["GET", "POST", "PUT", "DELETE"]:
                    err_msg = "{} has not been implemented".format(method)
                    print(err_msg)
                    raise NotImplementedError(err_msg)
                else:
                    if method == 'PUT' and self.__web_dav_enabled:
                        web_dav.create(uri, request.body)
                        response = Response(conn).set_status(201)
                        response.send()

                    elif method == 'DELETE' and self.__web_dav_enabled:
                        web_dav.delete(uri)
                        response = Response(conn).set_status(204)
                        response.send()

                    elif uri in self.__router[method]:
                        print("request received:", request)
                        callback = self.__router[method][uri]
                        response = Response(conn)
                        print("calling bound method")
                        result = callback(request=request, response=response)
                        print("complete")

                        if not response.body_set:
                            response.set_body(result)
                        if not response.status_set:
                            response.set_status(200)

                        print(response)
                        response.send()

                    else:
                        err_msg = "Endpoint not implemented {}:{}".format(method, uri)
                        print(err_msg)
                        raise RuntimeError(err_msg)
                    
            except RuntimeError as err:
                response = Response(conn).set_status(500)
                print('Error processing request: \n{}\n{}'.format(response, err))
                response.send()
                
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            