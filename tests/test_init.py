# -*- coding: utf-8 -*-
"""
    Tests for volt init command
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012-2016 Wibowo Arindrarto <bow@bow.web.id>
    :license: BSD

"""
from pathlib import Path

import yaml
from click.testing import CliRunner

from volt.cli import main
from volt.config import DEFAULT_CONFIG as DC


def test_init_default():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        result = runner.invoke(main, ["init"])
        wp = Path(fs)
        assert result.exit_code == 0
        # Expected 3 items: contents dir, templates dir, config
        assert len(list(wp.iterdir())) == 3
        assert wp.joinpath(DC["volt"]["contents_path"]).exists()
        assert wp.joinpath(DC["volt"]["templates_path"]).exists()
        assert wp.joinpath(DC["volt"]["assets_path"]).exists()
        config_path = wp.joinpath(DC["volt"]["config_name"])
        assert config_path.exists()
        # Config must be valid YAML
        with open(str(config_path), "r") as src:
            assert yaml.load(src)
