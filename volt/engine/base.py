# Volt base engine

import codecs
import glob
import os
import re
from datetime import datetime
from functools import partial
from inspect import isclass

import yaml

from volt import ConfigError, ContentError, ParseError
from volt.config import config


MARKUP = { '.html': 'html',
           '.md': 'markdown',
           '.markdown': 'markdown',
         }

# regex objects, so compilation is done efficiently
_RE_SPACES = re.compile(r'\s([A|a]n??)\s|_|\s+')
_RE_PRUNE = re.compile(r'A-|An-|[\!"#\$%&\'\(\)\*\+\,\./:;<=>\?@\[\\\]\^`\{\|\}~]')
_RE_MULTIPLE = re.compile(r'-+')
_RE_PERMALINK = re.compile(r'(.+?)/+(?!%)')


class BaseEngine(object):

    def __init__(self, unit_class=None):
        """Initializes the engine.

        Arguments:
        unit_class: content container class subclassing BaseUnit
        """
        if not issubclass(unit_class, BaseUnit):
            raise TypeError("Engine must be initialized with a content container class.")

        self.unit_class = unit_class
        self.units = []

    def globdir(self, directory, pattern='*', iter=False):
        """Returns glob or iglob results for a given directory.
        """
        pattern = os.path.join(directory, pattern)
        if iter:
            return glob.iglob(pattern)
        return glob.glob(pattern)

    def set_unit_paths(self, unit, site_dir, site_url, index_html=True):
        """Sets the permalink and absolute file path for the given unit.

        Arguments:
        unit: BaseUnit instance whose path and URL are to be set
        site_dir: absolute filesystem path to the output site directory
        site_url: static site URL, usually set in config.SITE
        index_html: boolean indicating output file name;  if False then
            the output file name is the '%s.html' where %s is the last
            string of the unit's permalist

        Output file defaults to 'index' so each unit will be written to
        'index.html' in its path. This allows nice URLs without fiddling
        the .htaccess too much.
        """
        path = [site_dir]
        url = [site_url]
        permalist = unit.permalist

        # set permalink
        # we don't want double slashes in URL, so remove empty strings
        url.extend(filter(None, unit.permalist))
        # if index_html is False, then we have to refer to the file
        # directly in the permalink
        if index_html:
            url[-1] = url[-1] + '/'
        else:
            url[-1] = url[-1] + '.html'
        setattr(unit, 'permalink', '/'.join(url))

        # set absolute path
        path.extend(unit.permalist)
        if index_html:
            path.append('index.html')
        else:
            path[-1] = path[-1] + '.html'
        setattr(unit, 'path', os.path.join(*(path)))

    def process_units(self):
        """Process the the units used to initialize the engine and use the results to fill self.units.
        """
        raise NotImplementedError("Subclasses must implement process_units().")

    def create_dirs(self):
        """Creates all required directories in the site folder.
        """
        raise NotImplementedError("Subclasses must implement create_dirs().")

    def build_paths(self):
        """Builds all the required URLs.
        """
        raise NotImplementedError("Subclasses must implement build_paths().")

    def write_single_unit(self):
        """Writes a single BaseUnit object to an output file.
        """
        raise NotImplementedError("Subclasses must implement write_single_unit().")

    def write_multiple(self):
        """Writes an output file composed of multipe BaseUnit object.
        """
        raise NotImplementedError("Subclasses must implement write_multiple().")

    def run(self):
        """Starts the engine processing.
        """
        raise NotImplementedError("Subclasses must implement run().")


class BaseUnit(object):

    def __init__(self, id):
        """Initializes BaseUnit instance.

        Arguments:
        id: any string that refers to the BaseUnit instance exclusively
        """
        self.id = id

    def __repr__(self):
        return str(self.__dict__)

    @property
    def fields(self):
        return self.__dict__.keys()

    # convenience methods
    open_text = partial(codecs.open, encoding='utf8')
    as_datetime = datetime.strptime
    get_display_time = datetime.strftime

    def parse_yaml(self, string):
        """Parses the yaml string.

        Arguments:
        string: yaml-formatted string

        This is a thin wrapper for yaml.load, so it's more convenient
        for subclassing xUnits to parse yaml contents.
        """
        # why can't this be assigned directly like the other wrappers?
        return yaml.load(string)

    def check_protected(self, field, prot):
        """Raises ContentError if field is present in protected.
        
        Arguments:
        field: string to check against prot
        prot: list containing protected fields
        """
        if field in prot:
            raise ContentError(\
                    "'%s' should not define the protected header field '%s'" % \
                    (self.id, field))

    def check_required(self, req):
        """Check if all the required header fields are present.

        Arguments:
        req: iterable that contains required header fields
        """
        for field in req:
            if not hasattr(self, field):
                raise ContentError(\
                        "Required header field '%s' is missing in '%s'." % \
                        (field, self.id))

    def as_list(self, field, sep):
        """Transforms a comma-separated tags or categories string into a list.

        Arguments:
        fields: string to transform into list
        sep: field subitem separator
        """
        return list(set(filter(None, field.strip().split(sep))))

    def set_markup(self, markup_dict):
        """Sets the markup language into a header key-value pair.

        Arguments:
        markup_dict: dictionary with file extensions as keys and
            their corresponding markup language as values
        """
        if not hasattr(self, 'markup'):
            ext = os.path.splitext(self.id)[1].lower()
            try:
                setattr(self, 'markup', markup_dict[ext])
            except:
                setattr(self, 'markup', 'html')
        setattr(self, 'markup', getattr(self, 'markup').lower())
        if getattr(self, 'markup') not in markup_dict.values():
            raise ContentError("Markup language '%s' is not supported." % \
                    getattr(self, 'markup'))

    def slugify(self, string):
        """Returns a slugified version of the given string.

        Arguments:
        string: string to transform into slug
        """
        string = string.strip()

        # replace spaces, etc with dash
        string = re.sub(_RE_SPACES, '-', string)

        # remove english articles, bad chars, and dashes in front and end
        string = re.sub(_RE_PRUNE, '', string)

        # warn if there are non-ascii chars
        assert string.decode('utf8') == string

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

        Arguments:
        pattern: string replacement pattern
        unit_base_url: base URL of the engine, to be appended in front of each
            unit URL

        The pattern argument may refer to the current object's attributes by
        enclosing them in square brackets. If the referred instance attribute 
        is a datetime object, it must be formatted by specifying a string format
        argument.

        Here are several examples of a valid permalink pattern:
        - '{time:%Y/%m/%d}/{slug}'
        - '{time:%Y}/post/{time:%d}/blog/{id}'
        """
        # raise exception if there are spaces?
        if pattern != pattern.replace(' ',''):
            raise ContentError("Permalink in '%s' contains whitespace(s)." \
                    % self.id)
        
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
                    raise ContentError("'%s' has no '%s' attribute." % \
                            (self.id, cmp))
                if isinstance(getattr(self, cmp), datetime):
                    strftime = datetime.strftime(getattr(self, cmp), fmt)
                    permalist.extend(filter(None, strftime.split('/')))
                else:
                    permalist.append(self.slugify(getattr(self, cmp)))
            else:
                permalist.append(self.slugify(item))

        return [unit_base_url.strip('/')] + filter(None, permalist)


def get_class(mod, cls):
    """Returns a class defined in the given module that is a subclass of the given class.

    Arguments:
    cls: parent class of the class to return
    mod: module to be searched
    """
    objs = (getattr(mod, x) for x in dir(mod) if isclass(getattr(mod, x)))
    # return if class is not itself
    for item in objs:
        if item.__name__ != cls.__name__ and issubclass(item, cls):
            return item

get_engine = partial(get_class, cls=BaseEngine)
get_unit = partial(get_class, cls=BaseUnit)
