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
from typing import Dict, Generator, Iterator, List, Optional, cast

from jinja2 import Environment, FileSystemLoader

from .config import SiteConfig
from .targets import CopyTarget, PageTarget, Target
from .units import Unit
from .utils import Result, calc_relpath, load_template

__all__ = ["SiteNode", "SitePlan", "Site"]


class SiteNode:

    """Node of the :class:`SitePlan` tree."""

    __slots__ = ("path", "target", "children", "is_dir")

    def __init__(self, path: Path, target: Optional[Target] = None) -> None:
        """Initialize a site node.

        :param path: Path to the node.
        :param A target to be created in the site output directory.  If set to
            ``None``, represents a directory. Otherwise, the given value must be
            a subclass of :class:`Target`.

        """
        self.path = path
        self.target = target
        self.children: Optional[Dict[str, SiteNode]] = (
            None if target is not None else {}
        )
        self.is_dir = target is None

    def __contains__(self, value: str) -> bool:
        children = self.children or {}

        return self.is_dir and value in children

    def __iter__(self) -> Iterator["SiteNode"]:
        if not self.is_dir:
            return iter([])
        children = self.children or {}

        return iter(children.values())

    def add_child(self, key: str, target: Optional[Target] = None) -> None:
        """Add a child to the node.

        If a child with the given key already exists, nothing is done.

        :param str key: Key to given child.
        :param target: A target to be created in the site output directory.
            If set to ``None``, represents a directory. Otherwise, the given
            value must be a subclass of :class:`Target`.

        :raises TypeError: if the node represents a directory (does not have
            any children).

        """
        if not self.is_dir:
            raise TypeError("cannot add children to file node")
        # TODO: Adjustable behavior for targets with the same dest? For now
        #       just take the first one.
        children = self.children or {}
        if key in children:
            return
        children[key] = SiteNode(self.path.joinpath(key), target)
        self.children = children


class SitePlan:

    """The file and directory layout of the final built site.

    A site plan is essentially an n-ary tree whose nodes represent either
    directories or files to be created.

    """

    def __init__(self, site_dest_rel: Path) -> None:
        """Initialize a site plan.

        :param site_dest_rel: Relative path to the site destination directory
            from the current working directory.

        """
        self.site_dest_rel = site_dest_rel
        self._root = SiteNode(site_dest_rel)
        self._root_path_len = len(site_dest_rel.parts)

    def add_target(self, target: Target) -> Result[None]:
        """Add a target to the plan.

        :param target: A target to be created in the site
            output directory.

        :returns: Nothing upon successful target addition or an error message
            when target cannot be added.

        """
        # Ensure target dest is relative (to working directory!)
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
                    cur = cast(Dict[str, SiteNode], cur.children)[p]
                else:
                    cur.add_child(p, target)
            except TypeError:
                return Result.as_failure(
                    f"path of target item {str(cur.path.joinpath(p))!r}"
                    f" conflicts with {str(cur.path)!r}")

        return Result.as_success(None)

    def fnodes(self) -> Generator[SiteNode, None, None]:
        """Yield all file target nodes, depth-first."""

        # TODO: Maybe compress the paths so we don't have to iterate over all
        #       directory parts?
        nodes = [self._root]
        while nodes:
            cur = nodes.pop()
            nodes.extend(iter(cur))
            if not cur.is_dir:
                yield cur

    def dnodes(self) -> Generator[SiteNode, None, None]:
        """Yield the least number of directory nodes required to construct
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


class Site:

    """The static site."""

    def __init__(
        self,
        config: SiteConfig,
        template_env: Optional[Environment] = None,
    ) -> None:
        """Initialize the static site for building.

        :param config: The validated site configuration.
        :param The jinja2 template environment. If set to ``None``, a default
            environment will be created.

        """
        self.config = config
        self.template_env = template_env or Environment(
            loader=FileSystemLoader(str(config["templates_src"])),
            auto_reload=False, enable_async=True)

        self.plan = SitePlan(self.config["site_dest_rel"])

    def gather_units(self, ext: str = ".md") -> Result[List[Unit]]:
        """Traverse the root contents directory for unit source files.

        :param ext: Extension (dot included) of the unit source filenames.

        :returns: A list of gathered units or an error message indicating
            failure.

        """
        site_config = self.config
        unit = site_config["unit"]

        units = []
        for unit_path in site_config["contents_src"].glob(f"*{ext}"):
            res = unit.load(unit_path, site_config)
            if res.is_failure:
                return res
            units.append(res.data)

        return Result.as_success(units)

    def create_pages(self, units: List[Unit]) -> Result[List[PageTarget]]:
        """Create :class:`PageTarget` instances representing templated page
        targets.

        :param units: List of units to turn into pages.

        :returns: A list of created pages or an error message indicating
            failure.

        """
        rtemplate = load_template(self.template_env,
                                  self.config["unit_template"])
        if rtemplate.is_failure:
            return rtemplate

        pages = []
        dest_rel = self.config["site_dest_rel"]
        for unit in units:
            dest = dest_rel.joinpath(f"{unit.metadata['slug']}.html")
            rrend = PageTarget.from_template(unit, dest, rtemplate.data)
            if rrend.is_failure:
                return rrend
            pages.append(rrend.data)

        return Result.as_success(pages)

    def gather_copy_assets(self) -> List[CopyTarget]:
        """Create :class:`CopyTarget` instances representing simple
        copyable targets.

        :returns: A list of created copy targets.

        """
        items = []
        dest_rel = self.config["site_dest_rel"]
        src_rel = calc_relpath(self.config["assets_src"], self.config['cwd'])
        src_rel_len = len(src_rel.parts)

        entries = list(os.scandir(src_rel))
        while entries:
            de = entries.pop()
            if de.is_dir():
                entries.extend(os.scandir(de))
            else:
                dtoks = Path(de.path).parts[src_rel_len:]
                target = CopyTarget(Path(de.path), dest_rel.joinpath(*dtoks))
                items.append(target)

        return items

    def create_section_targets(self) -> Result[List[Target]]:
        """Create all targets from all sections."""
        targets: List[Target] = []
        for name, sec_conf in self.config["sections"].items():
            eng_class = sec_conf.pop("engine")
            eng = eng_class(sec_conf, self.template_env)
            rsp = eng.create_targets()
            if rsp.is_failure:
                return rsp
            targets.extend(rsp.data)
        return Result.as_success(targets)

    def build(self) -> Result[None]:
        """Build the static site in the destination directory.

        :returns: Nothing when site building completes successfully or an error
            message indicating failure.

        """
        runits = self.gather_units()
        if runits.is_failure:
            return runits

        rpages = self.create_pages(runits.data)
        if rpages.is_failure:
            return rpages

        rstargets = self.create_section_targets()
        if rstargets.is_failure:
            return rstargets

        assets = self.gather_copy_assets()
        plan = self.plan
        for target in chain(rpages.data, rstargets.data, assets):
            plan.add_target(target)

        cwd = self.config['cwd']
        for dn in plan.dnodes():
            cwd.joinpath(dn.path).mkdir(parents=True, exist_ok=True)

        for fn in plan.fnodes():
            target = fn.target
            if target is not None:
                wres = target.create()
                if wres.is_failure:
                    return wres

        return Result.as_success(None)
