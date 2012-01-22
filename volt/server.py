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
from socket import error

from volt import __version__


class VoltHTTPRequestHandler(SimpleHTTPRequestHandler):

    server_version = 'VoltHTTPServer/' + __version__

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
        message = "[%s] %s\n" % (self.log_date_time_string(), format % args)

        if int(args[1]) >= 400:
            message = "%s%s%s" % ("\033[00;31m", message, "\033[m")
        elif int(args[1]) >= 300:
            message = "%s%s%s" % ("\033[00;32m", message, "\033[m")

        sys.stderr.write(message)

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

def run(args):
    """Runs the server.

    Arguments:
    args: Namespace object from argparse.ArgumentParser()
    """
    global options
    options = args

    # if server dir is not set, look for 'site' in current directory
    # otherwise, serve current directory
    if not options.server_dir:
        site_dir = os.path.join(os.getcwd(), 'site')
        if os.path.exists(site_dir):
            setattr(options, 'server_dir', site_dir)
        else:
            setattr(options, 'server_dir', os.getcwd())
    else:
        options.server_dir = os.path.abspath(options.server_dir)
        if not os.path.exists(options.server_dir):
            raise OSError("Directory does not exist.")

    sys.stderr.write("\n\033[00;32mVolt %s Development Server\033[m\n" % __version__)

    address = ('127.0.0.1', options.server_port)

    try:
        server = HTTPServer(address, VoltHTTPRequestHandler)
    except Exception, e:
        ERRORS = {
            13: "You don't have permission to access port %s." % 
                (options.server_port),
            98: "Port %s already in use." % (options.server_port),
        }
        try:
            error_message = ERRORS[e.args[0]]
        except (AttributeError, KeyError):
            error_message = str(e)
        sys.stderr.write("Error: %s\n" % error_message)
        sys.stderr.write("Aborting...\n\n")
        sys.exit(1)

    run_address, run_port = server.socket.getsockname()
    if run_address == '127.0.0.1':
        run_address = 'localhost'

    sys.stderr.write("Serving %s/\n" 
                     "Running at http://%s:%s/\n"
                     "CTRL-C to stop.\n\n" % 
                     (options.server_dir, run_address, run_port)
                    )

    try:
        server.serve_forever()
    except:
        server.shutdown()
        sys.stderr.write("\nServer stopped.\n\n")
        sys.exit(0)

    options.func(options)
