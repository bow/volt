# -*- coding: utf-8 -*-
"""
    volt.site
    ~~~~~~~~~

    Site-level functions and classes.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import os

from .config import DEFAULT_CONFIG, INIT_CONFIG_STR


class Site(object):

    """Representation of the static site."""

    def __init__(self, config):
        self.config = config

    def run_init(self, do_write_config):
        """Creates directories and files for a new site.

        This function may overwrite any preexisting files and or directories
        in the working directory. Ideally any checks on whether any overwrite
        should be performed has been done prior to calling this function.

        :returns: Error messages as a list of strings.

        """
        wp = str(self.config.work_path)
        if not os.access(wp, os.W_OK):
            return ["Directory '{0}' is not writable.".format(wp)]
        # Create directories
        self.config.contents_path.mkdir(parents=True, exist_ok=True)
        self.config.templates_path.mkdir(parents=True, exist_ok=True)
        self.config.assets_path.mkdir(parents=True, exist_ok=True)
        # Create initial YAML config file, if requested
        if do_write_config:
            fname = DEFAULT_CONFIG["volt"]["config_name"]
            with open(fname, "w") as target:
                print(INIT_CONFIG_STR, file=target)
        return []
