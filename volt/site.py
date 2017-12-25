# -*- coding: utf-8 -*-
"""
    volt.site
    ~~~~~~~~~

    Site-level functions and classes.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import os
from itertools import chain
from pathlib import Path

import jinja2.exceptions as j2exc

from .target import PageTarget, CopyTarget
from .utils import calc_relpath, Result


class SiteNode(object):

    __slots__ = ("path", "target", "children", "is_dir")

    def __init__(self, path, target=None):
        self.path = path
        self.target = target
        self.children = None if target is not None else {}
        self.is_dir = target is None

    def __contains__(self, value):
        return self.is_dir and value in self.children

    def __iter__(self):
        if not self.is_dir:
            return iter([])
        return iter(self.children.values())

    def add_children(self, part, target=None):
        if not self.is_dir:
            raise TypeError("cannot add children to file node")
        # TODO: Adjustable behavior for targets with the same dest? For now
        #       just take the first one.
        if part in self.children:
            return
        self.children[part] = SiteNode(self.path.joinpath(part), target)


class SitePlan(object):

    """Represents the file and directory layout of the final built site."""

    def __init__(self, site_dest_rel):
        self.site_dest_rel = site_dest_rel
        self._root = SiteNode(site_dest_rel)
        self._root_path_len = len(site_dest_rel.parts)

    def add_target(self, target):
        # Ensure target dest is relative (to project directory!)
        assert not target.dest.is_absolute()

        # Ensure target dest starts with project site_dest
        prefix_len = self._root_path_len
        assert target.dest.parts[:prefix_len] == self._root.path.parts

        rem_len = len(target.dest.parts) - prefix_len
        cur = self._root

        for idx, p in enumerate(target.dest.parts[prefix_len:], start=1):
            try:
                if idx < rem_len:
                    cur.add_children(p)
                    cur = cur.children[p]
                else:
                    cur.add_children(p, target)
            except TypeError:
                return Result.as_failure(
                    f"path of target item {str(cur.path.joinpath(p))!r}"
                    " conflicts with {str(cur.path)!r}")

    def fnodes(self):
        """Yields all file target nodes, depth-first."""
        # TODO: Maybe compress the paths so we don't have to iterate over all
        #       directory parts?
        nodes = [self._root]
        while nodes:
            cur = nodes.pop()
            nodes.extend(iter(cur))
            if not cur.is_dir:
                yield cur

    def dnodes(self):
        """Yields the least number of directory nodes required to construct
        the site.

        In other words, yields nodes whose children all represent file targets.

        """
        nodes = [self._root]
        while nodes:
            cur = nodes.pop()
            children = list(iter(cur))
            fnodes = [c for c in children if not c.is_dir]
            if children and len(fnodes) == len(children):
                yield cur
            else:
                nodes.extend(children)


class Site(object):

    """Representation of the static site."""

    def __init__(self, config, template_env):
        self.config = config
        self.template_env = template_env

    def gather_units(self, pattern="*.md"):
        site_config = self.config
        unit_cls = site_config.unit_cls

        units = []
        for unit_path in site_config.contents_src.glob(pattern):
            res = unit_cls.load(unit_path, site_config)
            if res.is_failure:
                return res
            units.append(res.data)

        return Result.as_success(units)

    def create_pages(self, cwd):
        runits = self.gather_units()
        if runits.is_failure:
            return runits

        conf = self.config
        tname = conf.unit_template_fname
        try:
            template = self.template_env.get_template(tname)
        except j2exc.TemplateNotFound:
            return Result.as_failure(f"cannot find template {tname!r}")
        except j2exc.TemplateSyntaxError as e:
            return Result.as_failure(f"template {tname!r} has syntax"
                                     f" errors: {e.message}")

        pages = []
        dest_rel = calc_relpath(self.config.site_dest, cwd)
        for unit in runits.data:
            dest = dest_rel.joinpath(f"{unit.metadata.slug}.html")
            rrend = PageTarget.from_template(unit, dest, template)
            if rrend.is_failure:
                return rrend
            pages.append(rrend.data)

        return Result.as_success(pages)

    def gather_copy_assets(self, cwd):
        items = []
        src_rel = calc_relpath(self.config.assets_src, cwd)
        dest_rel = calc_relpath(self.config.site_dest, cwd)
        src_rel_len = len(src_rel.parts)

        entries = list(os.scandir(src_rel))
        while entries:
            de = entries.pop()
            if de.is_dir():
                entries.extend(os.scandir(de))
            else:
                dtoks = Path(de.path).parts[src_rel_len:]
                target = CopyTarget(de.path, dest_rel.joinpath(*dtoks))
                items.append(target)

        return Result.as_success(items)

    def build(self, cwd):
        rpages = self.create_pages(cwd)
        if rpages.is_failure:
            return rpages

        rstats = self.gather_copy_assets(cwd)
        if rstats.is_failure:
            return rstats

        plan = SitePlan(calc_relpath(self.config.site_dest, cwd))

        for target in chain(rpages.data, rstats.data):
            plan.add_target(target)

        for dn in plan.dnodes():
            cwd.joinpath(dn.path).mkdir(parents=True, exist_ok=True)

        for fn in plan.fnodes():
            try:
                fn.target.write()
            except OSError as e:
                return Result.as_failure(
                    f"cannot write target {str(target.dest)!r}:"
                    f" {e.strerror}")

        return Result.as_success(None)
