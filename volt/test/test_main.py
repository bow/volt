# -*- coding: utf-8 -*-
"""
-------------------
volt.test.test_main
-------------------

Tests for the volt.main module.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import os
import shutil
import sys
import unittest

from mock import patch, call, MagicMock

from volt import VERSION, main
from volt.config import UnifiedConfigContainer
from volt.test import make_uniconfig_mock, FIXTURE_DIR, USER_DIR, INSTALL_DIR


COMMANDS = ['demo', 'ext', 'gen', 'init', 'serve', 'version']
CMD_INIT_DIR = os.path.join(FIXTURE_DIR, 'test_init')
CMD_DEMO_DIR = os.path.join(FIXTURE_DIR, 'test_demo')

UniConfig_mock = make_uniconfig_mock()


@patch.object(main, 'logging', MagicMock())
@patch.object(main.Runner, 'build_logger', MagicMock())
@patch.object(main, 'CONFIG', UniConfig_mock)
@patch.object(main, 'console')
class MainCases(unittest.TestCase):

    def test_cmd_ok(self, console_mock):
        commands = ['init', 'demo', 'gen', 'serve', 'version']
        for cmd in commands:
            with patch.object(main.Runner, 'run_%s' % cmd) as run_cmd:
                main.main([cmd])
                self.assertEqual([call()], run_cmd.call_args_list)

    #FIXME
    # skip testing if python version is <= 2.6, since argparser subparser
    # addition seems to be in random order
    if not sys.version_info[:2] <= (2, 6):
        def test_cmd_invalid(self, console_mock):
            commands = ['engines', 'foo', '']
            for cmd in commands:
                exp_call = call(\
                        "\nError: invalid choice: '%s' (choose from '%s')" % \
                        (cmd, "', '".join(COMMANDS)), color='red', is_bright=True)
                self.assertRaises(SystemExit, main.main, [cmd])
                self.assertEqual(exp_call, console_mock.call_args)

    def test_cmd_subcmd_ok(self, console_mock):
        commands = {'ext': ['engine', 'plugin', 'widget']}
        for cmd in commands:
            with patch.object(main.Runner, 'run_%s' % cmd) as run_cmd:
                for subcmd in commands[cmd]:
                    main.main([cmd, subcmd])
                self.assertEqual(call(), run_cmd.call_args)
                self.assertRaises(SystemExit, main.main, [cmd])

    def test_version_ok(self, console_mock):
        for path in (FIXTURE_DIR, USER_DIR, INSTALL_DIR):
            os.chdir(path)
            before = os.listdir(path)
            main.main(['version'])
            self.assertEqual(before, os.listdir(path))
            self.assertEqual(call('Volt %s' % VERSION), console_mock.call_args)

    @patch('volt.config.os.getcwd', return_value=FIXTURE_DIR)
    def test_init_demo_nonempty_dir(self, getcwd_mock, console_mock):
        before = os.listdir(FIXTURE_DIR)
        cmds = ['init', 'demo']

        for cmd in cmds:
            self.assertRaises(SystemExit, main.main, [cmd])
            exp_call = call("Error: 'volt %s' must be "
                    "run inside an empty directory." % cmd, \
                    color='red', is_bright=True)
            self.assertEqual(exp_call, console_mock.call_args)
            self.assertEqual(before, os.listdir(FIXTURE_DIR))


@patch.object(main, 'logging', MagicMock())
@patch.object(main.Runner, 'build_logger', MagicMock())
@patch.object(main, 'console')
class MainNoConfigCases(unittest.TestCase):

    def test_cmd_nonvolt_dir(self, console_mock):
        cmds = ['gen', 'serve']
        call2 = call("Start a Volt project by running 'volt init' inside an "
                     "empty directory.")

        for cmd in cmds:
            call1 = call("Error: You can only run 'volt %s' inside a Volt "
                         "project directory." % cmd, color='red', is_bright=True)
            before = os.listdir(FIXTURE_DIR)
            os.chdir(FIXTURE_DIR)
            self.assertRaises(SystemExit, main.main, [cmd])
            self.assertEqual(before, os.listdir(FIXTURE_DIR))
            self.assertEqual([call1, call2], console_mock.call_args_list)
            console_mock.reset_mock()


@patch.object(main, 'logging', MagicMock())
@patch.object(main.Runner, 'build_logger', MagicMock())
@patch.object(main, 'console')
class MainInitCases(unittest.TestCase):

    def setUp(self):
        self.console_call = call('\nVolt project started. Have fun!\n', is_bright=True)

    def tearDown(self):
        if os.path.exists(CMD_INIT_DIR):
            shutil.rmtree(CMD_INIT_DIR)
        # to reset main.CONFIG since it has been loaded with init's voltconf.py
        setattr(main, 'CONFIG', UnifiedConfigContainer())

    def run_init(self):
        if os.path.exists(CMD_INIT_DIR):
            shutil.rmtree(CMD_INIT_DIR)
        os.mkdir(CMD_INIT_DIR)
        os.chdir(CMD_INIT_DIR)
        main.main(['init'])

    def test_init_ok(self, console_mock):
        before = ['voltconf.py', 'contents/.placeholder', 'templates/base.html',
                  'templates/index.html', 'templates/assets/.placeholder',]
        before = [os.path.abspath(os.path.join(CMD_INIT_DIR, x)) for x in before]

        self.run_init()

        walk = list(os.walk(CMD_INIT_DIR))
        after = [os.path.join(d[0], f) for d in walk for f in d[2] if not f.endswith('.pyc')]
        [x.sort() for x in before, after]

        self.assertEqual(before, after)
        self.assertEqual([self.console_call], console_mock.call_args_list)

    @patch.object(main, 'generator', MagicMock())
    def test_init_gen_ok(self, console_mock):
        call2 = call('All engines are inactive -- nothing to generate.', \
                color='red', is_bright=True)

        self.run_init()
        before = [x for x in os.listdir(CMD_INIT_DIR) if not x.endswith('.pyc')]
        main.main(['gen'])
        after = [x for x in os.listdir(CMD_INIT_DIR) if not x.endswith('.pyc')]
        [x.sort() for x in before, after]

        self.assertEqual(before, after)
        self.assertEqual([self.console_call, call2], console_mock.call_args_list)

    @patch.object(main, 'server', MagicMock())
    @patch.object(main, 'generator', MagicMock())
    def test_init_serve_ok(self, console_mock):
        call2 = call('All engines are inactive -- nothing to generate.', \
                color='red', is_bright=True)
        call3 = call('Site directory not found -- nothing to serve.', \
                color='red', is_bright=True)

        self.run_init()
        before = [x for x in os.listdir(CMD_INIT_DIR) if not x.endswith('.pyc')]
        main.main(['serve'])
        after = [x for x in os.listdir(CMD_INIT_DIR) if not x.endswith('.pyc')]
        [x.sort() for x in before, after]

        self.assertEqual(before, after)
        self.assertEqual([self.console_call, call2, call3], console_mock.call_args_list)


@patch.object(main, 'logging', MagicMock())
@patch.object(main.Runner, 'build_logger', MagicMock())
@patch.object(main, 'console')
class MainDemoCases(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(CMD_DEMO_DIR):
            shutil.rmtree(CMD_DEMO_DIR)
        # to reset main.CONFIG since it has been loaded with demo's voltconf.py
        setattr(main, 'CONFIG', UnifiedConfigContainer())

    def prep_demo(self):
        if os.path.exists(CMD_DEMO_DIR):
            shutil.rmtree(CMD_DEMO_DIR)
        os.mkdir(CMD_DEMO_DIR)
        os.chdir(CMD_DEMO_DIR)

    @patch.object(main.server.VoltHTTPServer, 'serve_forever')
    def test_demo_ok(self, serveforever_mock, console_mock):
        exp_call = call('\nPreparing your lightning-speed Volt tour...', is_bright=True)

        self.prep_demo()
        self.assertFalse(os.path.exists(os.path.join(CMD_DEMO_DIR, 'site')))
        self.assertRaises(SystemExit, main.main, ['demo'])
        self.assertTrue(os.path.exists(os.path.join(CMD_DEMO_DIR, 'site')))

        self.assertEqual([exp_call], console_mock.call_args_list)
        self.assertEqual([call()], serveforever_mock.call_args_list)
