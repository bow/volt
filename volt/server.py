#!/usr/bin/env python

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
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler


__version__ = "0.1"

parser = argparse.ArgumentParser()

parser.add_argument('-p', '--port', action='store', dest='server_port',
                     default=8000, help='Sets the static server port', type=int)
parser.add_argument('-d', '--dir', action='store', dest='server_dir',
                     default=os.path.abspath(os.path.join(os.getcwd(), 'site')),
                     help='Sets the directory to serve')

class VoltHTTPRequestHandler(SimpleHTTPRequestHandler):

    server_version = 'VoltHTTP' + __version__

    def __init__(self, *args, **kwargs):
        self.base_dir = options.server_dir
        SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)

    def log_error(self, format, *args):
        """Logs the error.

        Overwritten to unclutter log message.
        """
        pass

    def log_message(self, format, *args):
        """Prints the log message.

        Overrides parent log_message to provide a more compact output.

        """
        sys.stderr.write("[%s] %s\n" % 
                         (self.log_date_time_string(), format % args))

    def log_request(self, code='-', size='-'):
        """Logs the accepted request.

        Overrides parent log_request so 'size' can be set dynamically.

        """
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
        """Returns filesystem path of from requests.

        Overrides parent translate_path to enable custom directory setting.

        """
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = self.base_dir
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        # set file path as attribute, to get size in log_request()
        self.file_path = path
        return self.file_path

def main():
    
    ### HACK, fix later
    global options
    options = parser.parse_args()

    address = ('127.0.0.1', options.server_port)
    
    print "\nVolt v%s Development Server" % (__version__)

    server = HTTPServer(address, VoltHTTPRequestHandler)

    running_address, running_port = server.socket.getsockname()
    if running_address == '127.0.0.1':
        running_address = 'localhost'

    print "Serving %s/" % (os.path.abspath(options.server_dir))
    print "Running at http://%s:%s/" % (running_address, running_port) 
    print "CTRL-C to stop.\n"

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print "\nServer stopped.\n"

if __name__ == '__main__':
    main()
