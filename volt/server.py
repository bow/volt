"""HTTP server for Volt's static output.

This module is just a simple wrapper for SimpleHTTPServer with more compact
log message and the option to set directory to serve. By default, it searches
for the "site" directory and serves the contents.
"""

import argparse
import os
import posixpath
import sys
import urllib
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import ThreadingTCPServer
from socket import error, getfqdn

from volt import util
from volt.config import config
from volt.main import __version__


class VoltHTTPServer(ThreadingTCPServer):
    """Volt HTTP Server
    """
    # copied from BaseHTTPServer.py since ThreadingTCPServer is used
    # instead of TCPServer
    allow_reuse_address = 1

    def server_bind(self):
        # overrides server_bind to store the server name.
        ThreadingTCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = getfqdn(host)
        self.server_port = port
                                                    

class VoltHTTPRequestHandler(SimpleHTTPRequestHandler):

    server_version = 'VoltHTTPServer/' + __version__

    def log_error(self, format, *args):
        # overwritten to unclutter log message.
        pass

    def log_message(self, format, *args):
        # overrides parent log_message to provide a more compact output.
        message = "[%s] %s\n" % (self.log_date_time_string(), format % args)

        if int(args[1]) >= 400:
            util.show_warning(message)
        elif int(args[1]) >= 300:
            util.show_notif(message)
        else:
            util.show_info(message)


    def log_request(self, code='-', size='-'):
        # overrides parent log_request so 'size' can be set dynamically.
        ### HACK, add code for 404 processing later
        if code <= 200:
            actual_file = os.path.join(self.file_path, 'index.html')
            if os.path.isdir(self.file_path):
                if os.path.exists(actual_file) or \
                   os.path.exists(actual_file[:-1]):
                    size = os.path.getsize(actual_file)
            else:
                size = os.path.getsize(self.file_path)
        self.log_message('"%s" %s %s',
                         self.requestline, str(code), str(size))

    def translate_path(self, path):
        # overrides parent translate_path to enable custom directory setting.
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = config.VOLT.SITE_DIR
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        # set file path as attribute, to get size in log_request()
        self.file_path = path
        return self.file_path


def run():
    """Runs the server.
    """
    address = ('127.0.0.1', config.CMD.server_port)
    try:
        server = VoltHTTPServer(address, VoltHTTPRequestHandler)
    except Exception, e:
        ERRORS = { 2: "Site directory '%s' not found" % config.VOLT.SITE_DIR,
                  13: "You don't have permission to access port %s" % 
                      (config.CMD.server_port),
                  98: "Port %s already in use" % (config.CMD.server_port)}
        try:
            error_message = ERRORS[e.args[0]]
        except (AttributeError, KeyError):
            error_message = str(e)
        util.show_error("Error: %s\n" % error_message)
        sys.exit(1)

    run_address, run_port = server.socket.getsockname()
    if run_address == '127.0.0.1':
        run_address = 'localhost'
    util.show_notif("\nVolt %s Development Server\n" % __version__)
    util.show_info("Serving %s/\n" 
                   "Running at http://%s:%s/\n"
                   "CTRL-C to stop.\n\n" % 
                   (config.VOLT.SITE_DIR, run_address, run_port))

    try:
        server.serve_forever()
    except:
        server.shutdown()
        util.show_notif("\nServer stopped.\n\n")
        sys.exit(0)
