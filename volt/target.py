# -*- coding: utf-8 -*-
"""
    volt.target
    ~~~~~~~~~~~

    Target-related classses and functions.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import filecmp
import shutil

import jinja2.exceptions as j2exc

from .utils import Result


class PageTarget(object):

    @classmethod
    def from_template(cls, src, dest, template):
        try:
            contents = template.render(unit=src)
        except j2exc.UndefinedError as e:
            return Result.as_failure(
                f"cannot render to {str(dest)!r} using {template.name!r}:"
                f" {e.message}")

        return Result.as_success(cls(src, dest, contents))

    def __init__(self, src, dest, contents):
        self.src = src
        self.dest = dest
        self.contents = contents

    @property
    def metadata(self):
        return self.src.metadata

    def write(self, project_dir):
        # TODO: check cache?
        project_dir.joinpath(self.dest).write_text(self.contents)


class StaticTarget(object):

    def __init__(self, src, dest):
        self.src = src
        self.dest = dest

    def write(self, project_dir):
        eff_src = project_dir.joinpath(self.src)
        eff_dest = project_dir.joinpath(self.dest)

        if not eff_dest.exists() or \
                not filecmp.cmp(str(eff_src), str(eff_dest), shallow=False):
            shutil.copy2(str(eff_src), str(eff_dest))
