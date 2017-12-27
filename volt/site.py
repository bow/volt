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
from typing import Generator, List

import jinja2.exceptions as j2exc
from jinja2 import Environment

from .config import SiteConfig
from .targets import PageTarget, CopyTarget
from .units import Unit
from .utils import calc_relpath, Result

__all__ = ["SiteNode", "SitePlan", "Site"]


class SiteNode(object):

    """Node of the :class:`SitePlan` tree."""

    __slots__ = ("path", "target", "children", "is_dir")

    def __init__(self, path: Path, target=None) -> None:
        """Initializes the site node.

        :param pathlib.Path path: Path to the node.
        :param object target: A target to be created in the site output
            directory. If set to ``None``, represents a directory. Otherwise,
            the given value must have a ``dest`` attribute / property that
            points to the location at which the target is to be created.

        """
        self.path = path
        self.target = target
        self.children = None if target is not None else {}
        self.is_dir = target is None

    def __contains__(self, value: str) -> bool:
        return self.is_dir and value in self.children

    def __iter__(self):
        if not self.is_dir:
            return iter([])
        return iter(self.children.values())

    def add_child(self, key: str, target=None) -> None:
        """Adds a child to the node.

        If a child with the given key already exists, nothing is done.

        :param str key: Key to given child.
        :param object target: A target to be created in the site output
            directory. If set to ``None``, represents a directory. Otherwise,
            the given value must have a ``dest`` attribute / property that
            points to the location at which the target is to be created.
        :raises TypeError: if the node represents a directory (does not have
            any children).

        """
        if not self.is_dir:
            raise TypeError("cannot add children to file node")
        # TODO: Adjustable behavior for targets with the same dest? For now
        #       just take the first one.
        if key in self.children:
            return
        self.children[key] = SiteNode(self.path.joinpath(key), target)


class SitePlan(object):

    """The file and directory layout of the final built site.

    A site plan is essentially an n-ary tree whose nodes represent either
    directories or files to be created.

    """

    def __init__(self, site_dest_rel: Path) -> None:
        """Initializes the site plan.

        :param pathlib.Path site_dest_rel: Relative path to the site
            destination directory from the current working directory.

        """
        self.site_dest_rel = site_dest_rel
        self._root = SiteNode(site_dest_rel)
        self._root_path_len = len(site_dest_rel.parts)

    def add_target(self, target) -> Result[None]:
        """Adds a target to the plan.

        :param object target: A target to be created in the site output
            directory. It must have a ``dest`` attribute / property that
            points to the location at which the target is to be created.
        :returns: Nothing upon successful target addition or an error message
            when target cannot be added.
        :rtype: :class:`Result`.

        """
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
                    cur.add_child(p)
                    cur = cur.children[p]
                else:
                    cur.add_child(p, target)
            except TypeError:
                return Result.as_failure(
                    f"path of target item {str(cur.path.joinpath(p))!r}"
                    " conflicts with {str(cur.path)!r}")

        return Result.as_success(None)

    def fnodes(self) -> Generator[SiteNode, None, None]:
        """Yields all file target nodes, depth-first."""
        # TODO: Maybe compress the paths so we don't have to iterate over all
        #       directory parts?
        nodes = [self._root]
        while nodes:
            cur = nodes.pop()
            nodes.extend(iter(cur))
            if not cur.is_dir:
                yield cur

    def dnodes(self) -> Generator[SiteNode, None, None]:
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

    """The static site."""

    def __init__(self, config: SiteConfig, template_env: Environment) -> None:
        """Initializes the static site for building.

        :param volt.config.SiteConfig config: The validated site configuration.
        :param jinja2.Environment template_env: The jinja2 template
            environment.

        """
        self.config = config
        self.template_env = template_env

    def gather_units(self, ext: str=".md") -> Result[List[Unit]]:
        """Traverses the root contents directory for unit source files.

        :param str ext: Extension (dot included) of the unit source filenames.
        :returns: A list of gathered units or an error message indicating
            failure.
        :rtype: :class:`Result`

        """
        site_config = self.config
        unit = site_config.unit

        units = []
        for unit_path in site_config.contents_src.glob(f"*{ext}"):
            res = unit.load(unit_path, site_config)
            if res.is_failure:
                return res
            units.append(res.data)

        return Result.as_success(units)

    def create_pages(self, cwd: Path) -> Result[List[PageTarget]]:
        """Creates :class:`PageTarget` instances representing templated page
        targets.

        :param pathlib.Path cwd: Path to the directory from which Volt is run.
        :returns: A list of created pages or an error message indicating
            failure.
        :rtype: :class:`Result`

        """
        runits = self.gather_units()
        if runits.is_failure:
            return runits

        conf = self.config
        tname = conf.unit_template
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

    def gather_copy_assets(self, cwd: Path) -> Result[List[CopyTarget]]:
        """Creates :class:`CopyTarget` instances representing simple
        copyable targets.

        :param pathlib.Path cwd: Path to the directory from which Volt is run.
        :returns: A list of created copy targets or an error message indicating
            failure.
        :rtype: :class:`Result`

        """
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

    def build(self, cwd: Path) -> Result[None]:
        """Builds the static site in the destination directory.

        :param pathlib.Path cwd: Path to the directory from which Volt is run.
        :returns: Nothing when site building completes successfully or an error
            message indicating failure.
        :rtype: :class:`Result`

        """
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
            wres = fn.target.create()
            if wres.is_failure:
                return wres

        return Result.as_success(None)
