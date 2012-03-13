# -*- coding: utf-8 -*-
"""
----------------
volt.engine.unit
----------------

Units are represent a single resource used during site generation, for example
a blog post or an image.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import codecs
import os
import re
from datetime import datetime
from functools import partial

import yaml

from volt.config import CONFIG


# regex objects, so compilation is done more efficiently
_RE_DELIM = re.compile(r'^---$', re.MULTILINE)
_RE_SPACES = re.compile(r'\s([A|a]n??)\s|_|\s+')
_RE_PRUNE = re.compile(r'A-|An-|[\!"#\$%&\'\(\)\*\+\,\./:;<=>\?@\[\\\]\^`\{\|\}~]')
_RE_MULTIPLE = re.compile(r'-+')
_RE_PERMALINK = re.compile(r'(.+?)/+(?!%)')


class ContentError(Exception):
    """Base exception for content-related error."""
    pass

class HeaderFieldError(ContentError):
    """Raised if a unit header field defines a protected field."""
    pass

class PermalinkTemplateError(ContentError):
    """Raised if a header field value defined in the permalink template is not found."""
    pass

class ParseError(ContentError):
    """Raised if a content-parsing related error occurs."""
    pass


class Unit(object):

    """Base Volt Unit class.

    The unit class represent a single resource used for generating the site,
    such as a blog post, an image, or a regular plain text file.

    """

    def __init__(self, id):
        """Initializes a unit instance.

        Args:
            id - String that refers exclusively to the unit. For example,
                if the resource is a text file then id can be the file path.

        """
        self.id = id

    def __repr__(self):
        return '%s(id=%s)' % (self.__class__.__name__, self.id)

    @property
    def fields(self):
        """Returns the unit namespace."""
        return self.__dict__.keys()

    # convenience methods
    open_text = partial(codecs.open, encoding='utf-8')
    as_datetime = datetime.strptime
    get_display_time = datetime.strftime

    def parse_yaml(self, string):
        """Parses the YAML string into a dictionary object.

        Args:
            string - YAML-formatted string

        This is a thin wrapper for yaml.load, so it's more convenient
        for subclassing unit classes to parse YAML contents.

        """
        # why can't this be assigned directly like the other wrappers?
        return yaml.load(string)

    def check_protected(self, field, prot):
        """Checks if the given field can be set by the user or not.
        
        Args:
            field - String to check against the list containing protected fields.
            prot - Iterable containing protected fields.

        """
        if field in prot:
            raise HeaderFieldError("'%s' should not define the protected "
                               " header field '%s'" % (self.id, field))

    def check_required(self, req):
        """Checks if all the required header fields are present.

        Args:
            req -  Iterable that returns required header fields.

        """
        for field in req:
            if not hasattr(self, field):
                raise HeaderFieldError("Required header field '%s' is "
                                   "missing in '%s'." % (field, self.id))

    def as_list(self, field, sep):
        """Transforms a comma-separated tags or categories string into a list.

        Args:
            fields - String to transform into list.
            sep - String used to split fields into list.

        """
        return list(set(filter(None, field.strip().split(sep))))

    def slugify(self, string):
        """Returns a slugified version of the given string.

        Args:
            string - String to transform into slug.

        """
        string = string.strip()

        # replace spaces, etc with dash
        string = re.sub(_RE_SPACES, '-', string)

        # remove english articles, bad chars, and dashes in front and end
        string = re.sub(_RE_PRUNE, '', string)

        # raise exception if there are non-ascii chars
        try:
            string.decode('ascii')
        except UnicodeDecodeError:
            raise ContentError("Slug in '%s' contains non-ascii characters." \
                               % self.id)

        # slug should not begin or end with dash or contain multiple dashes
        string = re.sub(_RE_MULTIPLE, '-', string)

        # and finally, we string preceeding and succeeding dashes
        string = string.lower().strip('-')

        # raise exception if slug results in an empty string
        if not string:
            raise ContentError("Slug for '%s' is an empty string." % self.id)

        return string

    def get_permalist(self, pattern, unit_base_url='/'):
        """Returns a list of strings which will be used to construct permalinks.

        Args:
            pattern - String replacement pattern.

        Keyword Args:
            unit_base_url - Base URL of the engine, to be appended in front of each
                unit URL.

        The pattern argument may refer to the current object's attributes by
        enclosing them in square brackets. If the referred instance attribute 
        is a datetime object, it must be formatted by specifying a string format
        argument.

        Several examples of a valid permalink pattern:
        
        '{time:%Y/%m/%d}/{slug}'
            Returns, for example, ['2009', '10', '04', 'the-slug']

        'post/{time:%d}/{id}'
            Returns, for example,  ['post', '04', 'item-103']

        """
        # strip preceeding '/' but make sure ends with '/'
        pattern = pattern.strip('/') + '/'

        # get all permalink components and store into list
        perms = re.findall(_RE_PERMALINK, pattern)

        # process components that are enclosed in {}
        permalist = []
        for item in perms:
            if item[0] == '{' and item[-1] == '}':
                cmp = item[1:-1]
                if ':' in cmp:
                    cmp, fmt = cmp.split(':')
                if not hasattr(self, cmp):
                    raise PermalinkTemplateError("'%s' has no '%s' attribute." % \
                            (self.id, cmp))
                if isinstance(getattr(self, cmp), datetime):
                    strftime = datetime.strftime(getattr(self, cmp), fmt)
                    permalist.extend(filter(None, strftime.split('/')))
                else:
                    permalist.append(self.slugify(getattr(self, cmp)))
            else:
                permalist.append(self.slugify(item))

        return [unit_base_url.strip('/')] + filter(None, permalist)

    def set_paths(self, base_dir=None, abs_url=None, index_html_only=None):
        """Sets the permalink and absolute file path for the unit.

        Args:
            unit - Unit instance whose path and URL are to be set

        Keyword Args:
            base_dir - Absolute file system path to the output site directory
            abs_url - String of base absolute URL (e.g. http://foo.com)
            index_html_only -  Boolean indicating output file name;  if False
                then the output file name is '%s.html' where %s is the last
                string of the unit's permalist

        Output file defaults to 'index' so each unit will be written to
        'index.html' in its path. This allows for nice URLs without fiddling
        with .htaccess too much.

        """
        assert hasattr(self, 'permalist'), \
                "%s requires the 'permalist' attribute to be set first." % \
                self.__class__.__name__

        if abs_url is None:
            abs_url = CONFIG.SITE.URL
        if base_dir is None:
            base_dir = CONFIG.VOLT.SITE_DIR
        if index_html_only is None:
            index_html_only = CONFIG.SITE.INDEX_HTML_ONLY

        rel_url = ['']
        path = [base_dir]

        # set path and urls
        path.extend(self.permalist)
        rel_url.extend(filter(None, self.permalist))
        if index_html_only:
            rel_url[-1] = rel_url[-1] + '/'
            path.append('index.html')
        else:
            rel_url[-1] = rel_url[-1] + '.html'
            path[-1] = path[-1] + '.html'
        setattr(self, 'permalink', '/'.join(rel_url))
        setattr(self, 'permalink_abs', '/'.join([abs_url] + rel_url[1:]).strip('/'))
        setattr(self, 'path', os.path.join(*(path)))


class TextUnit(Unit):

    """Class representation of text resources.

    This unit represents resources whose metadata (YAML header) is contained
    in the same file as the content. Some examples of resources like this 
    is a single blog post or a single plain page. 

    """

    def __init__(self, fname, config):
        """Initializes TextUnit.

        Args:
            fname - Absolute path to the source file.
            config - Config object containing unit options.

        """
        Unit.__init__(self, fname)

        with self.open_text(self.id) as source:
            # open file and remove whitespaces
            read = filter(None, _RE_DELIM.split(source.read()))
            # header should be parsed by yaml into dict
            try:
                header = self.parse_yaml(read.pop(0))
            except IndexError:
                raise ParseError("Header not detected in '%s'." % fname)
            if not isinstance(header, dict):
                raise ParseError("Header format unrecognizable in '%s'." \
                        % fname)

            # set blog unit file contents as attributes
            for field in header:
                self.check_protected(field, config.PROTECTED)
                if field in config.FIELDS_AS_DATETIME:
                    header[field] = self.as_datetime(\
                            header[field], config.CONTENT_DATETIME_FORMAT)
                if field in config.FIELDS_AS_LIST:
                    header[field] = self.as_list(header[field], config.LIST_SEP)
                if field == 'slug':
                    header[field] = self.slugify(header[field])
                if isinstance(header[field], (int, float)):
                    header[field] = str(header[field])
                setattr(self, field.lower(), header[field])

            # content is everything else after header
            self.content = read.pop(0).strip()

        # check if all required fields are present
        self.check_required(config.REQUIRED)

        # set other attributes
        # if slug is not set in header, set it now
        if not hasattr(self, 'slug'):
            self.slug = self.slugify(self.title)
        # and set global values
        for field in config.GLOBAL_FIELDS:
            if not hasattr(self, field):
                setattr(self, field, config.GLOBAL_FIELDS[field])

        # set permalink components
        self.permalist = self.get_permalist(config.PERMALINK, config.URL)
        # set displayed time string
        if hasattr(self, 'time'):
            self.display_time = self.time.strftime(config.DISPLAY_DATETIME_FORMAT)

        # set paths
        self.set_paths()

    def __repr__(self):
        return 'TextUnit(id=%s)' % os.path.basename(self.id)
