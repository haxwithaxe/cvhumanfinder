import SimpleHTTPServer
import SocketServer
import sys
import json
import logging
from SimpleCV import Image
import humanfinder
from humanfinder import FakeCamera

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

PORT = int(sys.argv[1], 10)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('http')
hf_args = {'show':False, 'clean_plate':Image(humanfinder.conf.clean_plate)}
hf = humanfinder.HFHandler.start(**hf_args)

class HumansFound(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        logger.debug('received GET request')
        reply = hf.ask({'sample':0})
        logger.debug('replying: %s' % reply)
        f = StringIO()
	f.write(json.dumps({'data':reply}))
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = 'utf-8'
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            try:
                self.copyfile(f, self.wfile)
            finally:
                f.close()

handler = HumansFound
httpd = SocketServer.TCPServer(('', PORT), handler)
logger.debug('serving at port: %d' % PORT)
httpd.serve_forever()
