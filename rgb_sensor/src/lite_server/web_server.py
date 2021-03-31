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


def function_args(func):
    function_arguments = [i for i in dir(func) if not i.startswith('__')]
    return function_arguments

def get_function_kwargs(arg_list, request, response):
    """ Throws KeyError if arg is not available in body """
    kwarg_source = request.body if isinstance(request.body, dict) else {}
    kwarg_source.update({'request': request, 'response': response})
    kwargs = {
        arg_name: kwarg_source[arg_name]
        for arg_name in arg_list
    }
    return kwargs

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
            self.__router["POST"][uri] = (func, function_args(func))
            return func
        return wrapper

    def GET(self, uri):
        def wrapper(func):
            self.__router["GET"][uri] = (func, function_args(func))
            return func
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
                        callback, arg_list = self.__router[method][uri]
                        response = Response(conn)
                        print("calling bound method")
                        kwargs = get_function_kwargs(arg_list, request, response):
                        result = callback(**kwargs)
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
            