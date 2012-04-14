# -*- coding: utf-8 -*-
"""
----------------
volt.plugin.core
----------------

Core Volt plugin.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import abc
import os

from volt.config import CONFIG, Config
from volt.utils import path_import


class Plugin(object):

    """Plugin base class.

    Volt plugins are subclasses of Plugin that perform a set of operations
    to Unit objects of a given engine. They are executed after all
    Engines finish parsing their units and before any output files are
    written. Plugin execution is handled by the Generator object in
    volt.gen.

    During a Generator run, Volt tries first to look up a given plugin
    in the plugins directory in the project's root folder. Failing that,
    Volt will try to load the plugin from volt.plugins.

    Default settings for a Plugin object should be stored as a Config object
    set as a class attribute with the name DEFAULTS. Another class attribute
    named USER_CONF_ENTRY may also be defined. This tells the Plugin which
    Config object in the user's voltconf.py will be consolidated with the
    default configurations in DEFAULTS. Finally, all Plugin subclasses must
    implement a run method, which is the entry point for plugin execution
    by the Generator class.

    """

    __metaclass__ = abc.ABCMeta

    DEFAULTS = Config()

    USER_CONF_ENTRY = None

    def __init__(self):
        """Initializes Plugin."""

        self.config = Config(self.DEFAULTS)

    def prime(self):
        """Consolidates default plugin Config and user-defined Config."""

        # only override defaults if USER_CONF_ENTRY is defined
        if self.USER_CONF_ENTRY is not None:
            # get user config object
            conf_name = os.path.splitext(os.path.basename(CONFIG.VOLT.USER_CONF))[0]
            voltconf = path_import(conf_name, CONFIG.VOLT.ROOT_DIR)

            # use default Config if the user does not list any
            try:
                user_config = getattr(voltconf, self.USER_CONF_ENTRY)
            except AttributeError:
                user_config = Config()

            # to ensure proper Config consolidation
            if not isinstance(user_config, Config):
                raise TypeError("User Config object '%s' must be a Config instance." % \
                        self.USER_CONF_ENTRY)
            else:
                self.config.update(user_config)

    @abc.abstractmethod
    def run(self):
        """Runs the plugin."""
