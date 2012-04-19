# -*- coding: utf-8 -*-
"""
-----------
volt.server
-----------

Development server for Volt.

This module provides a multithreading HTTP server that subclasses
SocketServer.ThreadingTCPServer. The server can auto-regenerate the Volt site
after any file inside it is changed and a new HTTP request is sent. It can be
run from any directory inside a Volt project directory and will always return
resources relative to the Volt output site directory. If it is run outside of
a Volt directory, an error will be raised.

A custom HTTP request handler subclassing
SimpleHTTPServer.SimpleHTTPRequestHandler is also provided. The methods defined
in this class mostly alters the command line output. Processing logic is similar
to the parent class.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import logging
import os
import posixpath
import sys
import urllib
from functools import partial
from itertools import chain
from socket import getfqdn
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import ThreadingTCPServer

from volt import VERSION
from volt import generator
from volt.config import CONFIG
from volt.utils import console, LoggableMixin


console = partial(console, format="[srv] %s  %s\n")


class VoltHTTPServer(ThreadingTCPServer, LoggableMixin):

    """A simple multithreading HTTP server for Volt development."""

    # copied from BaseHTTPServer.py since ThreadingTCPServer is used
    # instead of TCPServer
    allow_reuse_address = 1

    def __init__(self, *args, **kwargs):
        """Initializes Volt HTTP server.

        In addition to performing BaseServer initialization, this method
        also polls the timestamp of all directories inside the Volt project
        directory except the site output directory. This is set as a self
        atttribute and will be used later to generate the site everytime
        a file inside these directories are modified.

        """
        self.last_mtime = self.check_dirs_mtime()
        ThreadingTCPServer.__init__(self, *args, **kwargs)
        self.logger.debug('created: %s' % type(self).__name__)

    def process_request(self, request, client_address):
        """Finishes one request by instantiating the handler class.

        Prior to handler class initialization, this method checks the latest
        timestamp of all directories inside the Volt project. If the result
        is higher than the prior timestamp (self.last_mtime), then the entire
        site will be regenerated.

        """
        latest_mtime = self.check_dirs_mtime()

        if self.last_mtime < latest_mtime:
            message = "Source file modification detected -- regenerating site"
            console(message, color='yellow')
            self.logger.debug(message)

            self.last_mtime = latest_mtime
            CONFIG.reset()
            generator.run()
            self.logger.debug('done: regenerating site')

        ThreadingTCPServer.process_request(self, request, client_address)

    def check_dirs_mtime(self):
        """Returns the latest timestamp of directories in a Volt project.

        This method does not check the site output directory since the user
        is not supposed to change the contents inside manually.

        """
        # we don't include the output site directory because it will have
        # higher mtime than the user-modified file
        # the root directory is also not included since it will have higher
        # mtime due to the newly created output site directory
        # but we do want to add voltconf.py, since the user might want to
        # check the effects of changing certain configs
        dirs = (x[0] for x in os.walk(CONFIG.VOLT.ROOT_DIR) if
                CONFIG.VOLT.SITE_DIR not in x[0] and CONFIG.VOLT.ROOT_DIR != x[0])

        files = [CONFIG.VOLT.USER_CONF]
        if os.path.exists(CONFIG.VOLT.USER_WIDGET):
            files.append(CONFIG.VOLT.USER_WIDGET)

        return max(os.stat(x).st_mtime for x in chain(dirs, files))

    def server_bind(self):
        # overrides server_bind to store the server name.
        ThreadingTCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = getfqdn(host)
        self.server_port = port
                                                    

class VoltHTTPRequestHandler(SimpleHTTPRequestHandler, LoggableMixin):

    """HTTP request handler of the Volt HTTP server.

    This request handler can only be used for serving files inside a Volt
    site directory, since its path resolution is relative to that  directory.
    In addition to that, the handler can display colored text output according
    to the settings in voltconf.py and outputs the size of the returned file
    in its HTTP log line. 404 error messages are suppressed to allow for more
    compact output.

    Consult the SimpleHTTPRequestHandler documentation for more information.

    """

    server_version = 'VoltHTTPServer/' + VERSION

    def log_error(self, format, *args):
        # overwritten to unclutter log message.
        pass

    def log_message(self, format, *args):
        # overrides parent log_message to provide a more compact output.
        message = format % args

        if int(args[1]) >= 400:
            console(message, color='red')
        elif int(args[1]) >= 300:
            console(message, color='cyan')
        else:
            console(message)
        
        self.logger.debug(message)

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

        format = '"%s" %s %s'
        args = (self.requestline[:-9], str(code), str(size))
        self.log_message(format, *args)

    def translate_path(self, path):
        # overrides parent translate_path to enable custom directory setting.
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = CONFIG.VOLT.SITE_DIR
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): 
                continue
            path = os.path.join(path, word)
        # set file path as attribute, to get size in log_request()
        self.file_path = path
        return self.file_path


def run():
    """Runs the HTTP server using options parsed by argparse, accessible
    via CONFIG.CMD."""

    logger = logging.getLogger('server')

    address = ('127.0.0.1', CONFIG.CMD.server_port)
    try:
        server = VoltHTTPServer(address, VoltHTTPRequestHandler)
    except Exception, e:
        ERRORS = { 2: "Site directory '%s' not found" % CONFIG.VOLT.SITE_DIR,
                  13: "You don't have permission to access port %s" % 
                      (CONFIG.CMD.server_port),
                  98: "Port %s already in use" % (CONFIG.CMD.server_port)}
        try:
            message = ERRORS[e.args[0]]
        except (AttributeError, KeyError):
            message = str(e)
        logger.error(message)
        sys.exit(1)

    run_address, run_port = server.socket.getsockname()
    if run_address == '127.0.0.1':
        run_address = 'localhost'

    message = "Volt %s Development Server" % VERSION
    console(message, is_bright=True)
    logger.debug(message)

    message = "Serving %s" % CONFIG.VOLT.SITE_DIR
    console(message)
    logger.debug(message)

    message = "Running at http://%s:%s" % (run_address, run_port)
    console(message)
    logger.debug(message)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    finally:
        sys.stdout.write("\n")
        message = "Server stopped"
        console(message)
        logger.debug(message)
        sys.stdout.write("\n")
        sys.exit(0)
