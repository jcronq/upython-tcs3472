import ujson

class Request():
    def __init__(self, conn):
        self._conn = conn

        self._method = None
        self._uri = None
        self._version = None
        self._header = {}
        self._body = None
        self._build_from_conn(conn)
    
    @property
    def method(self):
        return self._method

    @property
    def uri(self):
        return self._uri

    @property
    def version(self):
        return self._version

    @property
    def header(self):
        return self._header

    @property
    def body(self):
        return self._body

    def _build_from_conn(self, conn):
        recv_file = conn.makefile('rwb', 0)
        header_lines = []
        while True:
            line = recv_file.readline()
            # A single blank line seperates the Request header from the body
            if not line or line == b'\r\n':
                break
            else:
                header_lines.append(line)
        
        self._parse_header(header_lines)
        self._parse_body()


    def _parse_header(self, header_lines):
        request_line = str(header_lines.pop(0))[2:-5]
        print('request', request_line)
        stripped_request = request_line.strip()
        method, uri, version = stripped_request.split(' ')

        self._method = method
        self._uri = uri
        self._version = version
        
        for option in header_lines:
            header_key, header_value = str(option)[2:-5].split(': ')
            if header_key == 'Content-Lenght':
                header_value = int(header_value)
            self.header[header_key] = header_value
        
    def _parse_body(self):
        if 'Content-Length' in self._header:
            data = []
            contentLength = self._header['Content-Length']
            while contentLength > 0:
                getsize = 1024
                if contentLength < getsize:
                    getsize = contentLength
                data.append(self._conn.recv(getsize))
            
            if self._header['Content-Type'] == 'application/json':
                self._body = ujson.loads("".join(data))
            else:
                self._body = "".join(data)