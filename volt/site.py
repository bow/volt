# -*- coding: utf-8 -*-
"""
    volt.site
    ~~~~~~~~~

    Site-level functions and classes.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import os
from collections import OrderedDict

import toml

from .config import SessionConfig, CONFIG_FNAME
from .utils import Result


class Site(object):

    """Representation of a static site."""

    def __init__(self, config):
        self.config = config.site

    @classmethod
    def run_init(cls, target_wd, name, url, config_fname=CONFIG_FNAME):
        """Creates directories and files for a new site.

        This function may overwrite any preexisting files and or directories
        in the target working directory.

        :returns: Error messages as a list of strings.

        """
        if not os.access(str(target_wd), os.W_OK):
            return Result.as_failure(f"directory {target_wd} is not writable")

        # Bootstrap directories.
        bootstrap_conf = SessionConfig(target_wd).site
        bootstrap_conf.contents_src.mkdir(parents=True, exist_ok=True)
        bootstrap_conf.templates_src.mkdir(parents=True, exist_ok=True)
        bootstrap_conf.assets_src.mkdir(parents=True, exist_ok=True)

        # Create initial TOML config file.
        init_conf = OrderedDict([
            ("site", OrderedDict([
                ("name", name),
                ("url", url),
            ]))
        ])
        target_wd.joinpath(config_fname).write_text(toml.dumps(init_conf))

        return Result.as_success(None)
