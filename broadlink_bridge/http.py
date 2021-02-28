import http.server
import threading
from . import LOGGER, REGISTRY, SERVER
import base64

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = SERVER
    auth_string = ""

    def log_request(self, code='-', size='-'):
        LOGGER.debug('HTTP: %s code %s', self.requestline, code)

    def log_error(self, format, *args):
        LOGGER.warn('HTTP: %s %s', self.requestline, format%args)

    def send_error(self, code, message=None, explain=None):
        self.log_error("code %d, message %s", code, message)
        self.send_response(code, message)
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"broadlink\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def check_auth(self):
        if self.auth_string == "":
            return True

        if self.headers.get('Authorization') == None:
            return False


        if self.headers.get('Authorization') != 'Basic '+self.auth_string:
            return False
        
        return True

    def do_POST(self):
        
        if not self.check_auth():
            self.do_AUTHHEAD()
            return

        path = self.path
        if not path.startswith('/device/'):
            return self.send_error(404)
        path = path[8:]

        path = path.split('/')

        device_id = path[0]
        device = REGISTRY.find_device(device_id)
        if not device:
            return self.send_error(404, 'Device not found: ' + device_id)

        size = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(size)        
        try:
            if len(path)>=2 and path[1] == 'temperature':
                temp = device.check_temperature()
                self.send_response(200, 'OK')
                self.end_headers()
                self.wfile.write(str(temp).encode('utf-8'))
                return
            if not payload:
                return self.send_error(400, 'No payload')
            if device.transmit(payload):
                self.send_response(204, 'OK')
                self.end_headers()
                return
        except ValueError:
            pass
        self.send_error(400, 'Bad payload')

def httpd_start(port,user,password):
    if not port or port <= 0:
        LOGGER.info('HTTP server disabled')
        return False

    httpd = http.server.HTTPServer(('', port), Handler)
    httpd.request_queue_size = 10
    
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()

    if user != "":
        auth = user+':'+password
        auth_string_bytes = auth.encode("ascii") 
        auth_bytes = base64.b64encode(auth_string_bytes) 
        Handler.auth_string = auth_bytes.decode("ascii") 

    LOGGER.info('HTTP server started on port %s', port)
    return True