import re
import datetime
import socket
import typing
from time import sleep

class HttpProtocol:

    CRLF = '\r\n'

    def __init__(self, socket_buffer=None):
        if socket_buffer:
            self.sb = socket_buffer

    def parse_headers(self, headers_data: str) ->Dict[str, str]:
        headers = headers_data.strip().split(self.CRLF)
        parsed_headers = dict()
        for header_line in headers:
            try:
                header, data = header_line.split(': ', maxsplit=1)
                parsed_headers[header] = data
            except ValueError:
                raise ValueError #raise a meaningfull error
        return parsed_headers


    def download_payload(self, save_as, content_length):
        download_length = 0

        with open(save_as, 'wb') as download_file:
            while download_length < content_length:
                self.sb.recv()
                packet = self.sb.empty_buffer()
                if not packet:
                    return None
                download_length += len(packet)
                download_file.write(packet)

    def get_headers(self):
        '''
        Receive header data from socket
        '''
        response_msg = ''
        header_recv = False
        while not header_recv:
            self.sb.recv()
            while True:
                msg_buffer = self.sb.read_buffer(1).decode()
                if not msg_buffer:
                    break
                response_msg += msg_buffer
                if response_msg[-4:] == '\r\n\r\n':
                    header_recv = True
                    break
        return response_msg

    def send_data_chunks(self, chunk_size, file_handler, seek_start, seek_end):
        file_handler.seek(seek_start)
        while file_handler.tell() <= seek_end:
            data_chunk = file_handler.read(min(chunk_size, seek_end - file_handler.tell()))
            if not data_chunk:
                break
            self.sock.sendall(data_chunk)
            sleep(1)
        #file_handler.close()

    @staticmethod
    def find_server_and_resouce(url):
        '''
        Finds server, port and resorce path from url using regex
        regex_pattern -
            non-capturing group 1 : communication protocol
            capturing group 1: host
            non-capturing group 2: colon(:)
            capturing group 2: port number
            non-capturing group 3: slash(/) - unnecessary will rectify it later
            capturing group 3: path to resource
        '''
        regex_pattern = '^(?:\w+\:\/\/)?([^:\/?]+)(?:[\:]?)([0-9]*)(?:\/?)(.*)$'
        pattern_obj = re.compile(regex_pattern)
        assert (url.partition('://')[0] == 'http'), "Error! Script can only work for HTTP based servers."
        host, port, resource = pattern_obj.findall(url)[0]

        port = int(port) if port else 80 #assign default TCP port 80 if none assigned
        resource = '/' if not resource else resource

        return host, port, resource

class HttpRequest(HttpProtocol):

    REQ_METHOD = 'req_method'
    RESOURCE = 'resource'
    HTTP_VERSION = 'http_version'

    def __init__(self, *args, **kwargs):
        super(HttpRequest, self).__init__(*args, **kwargs)

    def parse_request(self, request_data):
        parsed_headers = self.parse_headers(request_data)
        req_method, resource,  http_version = unparsed_headers.pop().split()

        parsed_headers[REQ_METHOD] = req_method
        parsed_headers[RESOURCE] = resource
        parsed_headers[HTTP_VERSION] = http_version

        return parsed_headers


    def generate_request(self, req_method, resource, server_addr, data_range=None):
        request_line = "%s /%s HTTP/1.1%s" % (req_method, resource, self.CRLF)

        if data_range is not None:
            data_range = "bytes=" + data_range
        header_dict = {
            'User-Agent': 'Python Script',
            'Host': '%s' % (server_addr),
            'Accept': '*/*',
            'Range': data_range
        }
        request = (request_line + "".join("%s: %s%s" % (key, value, self.CRLF) for key, value in header_dict.items() if value is not None) + self.CRLF)
        return request

class HttpResponse(HttpProtocol):

    def __init__(self, *args, **kwargs):
        super(HttpResponse, self).__init__(*args, **kwargs)

    def generate_response(self, total_content_length, resp_status_msg, content_range=None):
        response_line = 'HTTP/1.1 %s%s' % (resp_status_msg, self.CRLF)
        time_now = datetime.datetime.now()
        if content_range is not None:
            a, b = map(int, content_range.split('-'))
            content_length = b-a
            content_range = 'bytes %s/%s' %  (content_range, total_content_length)
        else:
            content_length = total_content_length
        send_headers = { 'Server' : 'Python Script',
                         'Content-Length' : content_length,
                         'Content-Range' : content_range,
                         'Accept-Ranges' : 'bytes',
                         'Date' : time_now.strftime("%d %b %Y, %H:%M:%S GMT") }
        send_data = ''.join("%s: %s%s" % (key, value, self.CRLF) for key, value in send_headers.items() if value is not None)

        return response_line + send_data + self.CRLF


    def parse_response(self, response_data):
        parsed_headers, unparsed_headers = self.parse_headers(response_data)
        for line in unparsed_headers:
            try:
                http_version, resp_code, resp_status_msg = unparsed_headers.pop().split(" ", maxsplit=2)
            except ValueError:
                raise ValueError("Header of unknow format recieved!")
        parsed_headers['http-version'] = http_version
        parsed_headers['resp_code'] = resp_code
        parsed_headers['resp_status_msg'] = resp_status_msg
        return parsed_headers

class SocketBuffer:

    WAIT_TIME = 10 #in seconds
    BLOCK_SIZE = 2048 #in bytes
    CRLF = '\r\n'

    def __init__(self, sock):
        self.sock = sock
        self.data_buffer = b''
        self.sock.settimeout(self.WAIT_TIME)

    def readLine(self):
        data_recv = self.sock.recv(self.BLOCK_SIZE)
        line = ''
        seek = 0
        while data_recv[seek:seek+1].encode() != self.CRLF:
            line += data_recv[seek]
            seek += 1
        line += data_recv[seek:seek+1].encode()
        if self.BLOCK_SIZE > len(line):
            self.data_buffer = data_recv[seek+2:]
        return line

    def upload_from(self, file_handle):
        pass

    def download_to(self, file_handle):
        pass

    def empty_buffer(self):
        return_data = self.data_buffer
        self.data_buffer = b''
        return return_data

    def read_buffer(self, length):
        return_data = self.data_buffer[:length]
        self.data_buffer = self.data_buffer[length:]
        return return_data
