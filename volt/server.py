#!/usr/bin/env python

"""HTTP server for Volt's static output.

This module is just a simple wrapper for SimpleHTTPServer with more compact
log message and the option to set directory to serve. By default, it searches
for the "site" directory and serves the contents.

"""

import os
import posixpath
import sys
import urllib
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler


class VoltHTTPRequestHandler(SimpleHTTPRequestHandler):

    #server_version = 'VoltHTTP' + __version__

    def __init__(self, *args, **kwargs):
        self.base_dir = os.path.abspath(os.path.join(os.getcwd(), 'site'))
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
        if code / 100 != 3:
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
    
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 8000
    address = ('127.0.0.1', port)
    
    server = HTTPServer(address, VoltHTTPRequestHandler)
    sa = server.socket.getsockname()

    print "\nVolt development server running at %s:%s ..." % (sa[0], sa[1]) 
    print "Serving contents of %s." % ("directory")
    print "CTRL-C to stop.\n"

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print "\nServer stopped.\n"

if __name__ == '__main__':
    main()
