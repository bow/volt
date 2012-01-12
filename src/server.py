#!/usr/bin/env python

"""HTTP server for Volt's static output.

This module is just a simple wrapper for SimpleHTTPServer with more compact
log message, and ability to look for Volt's site output directory provided
the active directory is a subdirectory of Volt's root.

"""

import os
import sys
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler


class VoltHTTPRequestHandler(SimpleHTTPRequestHandler):

    #server_version = 'VoltHTTP' + __version__

    def __init__(self, *args, **kwargs):
        self.base_dir = self.find_base()
        SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)

    def find_base(self):
        """Returns the base directory for static site output.

        Made to enable server run from any subdirectory of Volt's root.

        """
        ### TODO-01
        ### after proper directory tree has been decided
        ### TEMP
        return os.getcwd()

    def log_message(self, format, *args):
        """Prints the log message.

        Overrides parent log_message to provide a more compact output.

        """
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format%args)) 

    ### TODO-01
    ### after proper directory tree has been decided
    ### TEMP
#    def translate_path(self):
#        """Returns filesystem path of from requests.
#
#        Overrides parent translate_path to enable output static site directory
#        lookup.
#
#        """

def main():
    
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 8000
    address = ('127.0.0.1', port)
    
    server = HTTPServer(address, VoltHTTPRequestHandler)
    sa = server.socket.getsockname()

    print "\nVolt development server running at %s:%s ..." % (sa[0], sa[1]) 
    print "CTRL-C to stop.\n"

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print "\nServer stopped.\n"

if __name__ == '__main__':
    main()
