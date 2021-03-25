import ujson

def content_type_header(content_type):
    return "Content-Type: {}".format(content_type)

STATUS_CODE_MAP = {
    '200': 'OK',
    '201': 'Created',
    '202': 'Accepted',
    '204': 'No Content',
    '400': 'Bad Request',
    '500': 'Internal Server Error',
}

class Response:
    def __init__(self, conn):
        self._conn = conn
        self.version = 1.1
        self._status = None
        self._status_txt = None
        self._headers = []
        self._body = None

        self.body_set = False
    
    @property
    def status_set(self):
        return self._status is not None 
    
    def send(self):
        self._conn.send(str(self))
        self._conn.close()
    
    def add_header(self, header_txt):
        self._headers.append(header_txt)
        return self
    
    def set_body(self, body):
        self.body_set = True
        if body is None:
            return self
        if isinstance(body, str):
            self._body = body
            self.add_header(content_type_header("text/html"))
        else:
            self._body = ujson.dumps(body)
            self.add_header(content_type_header("application/json"))
        return self

    def set_status(self, status_code, status_msg=None):
        self._status = status_code
        if status_msg is not None:
            self._status_txt = status_msg
        elif str(status_code) not in STATUS_CODE_MAP and status_msg is None:
            raise RuntimeError("status_msg must be set when supplying a non-default status_code")
        else:
            self._status_txt = STATUS_CODE_MAP.get(str(status_code), "Internal Server Error")
        return self

    @property
    def header(self):
        return "\r\n".join(self._headers)
    
    @property
    def status(self):
        return "{} {}".format(self._status, self._status_txt)

    @property
    def status_line(self):
        return "HTTP/{} {}".format(self.version, self.status)

    def __repr__(self):
        if self._body is None:
            return "{}\r\n{}\r\n".format(self.status_line, self.header)
        return "{}\r\n{}\r\n\r\n{}".format(self.status_line, self.header, self._body)

    def __str__(self):
        return self.__repr__()
