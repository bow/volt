# Volt base engine

import codecs
import glob
import os
import re
from datetime import datetime
from functools import partial

import yaml

from volt import ContentError, ParseError
from volt.config import SessionConfig
from volt.util import grab_class


MARKUP = { '.html': 'html',
           '.md': 'markdown',
           '.markdown': 'markdown',
         }

# regex objects, so compilation is done efficiently
# for TextUnit header delimiter
_RE_DELIM = re.compile(r'^---$', re.MULTILINE)
# for Engine.slugify
_RE_SPACES = re.compile(r'\s([A|a]n??)\s|_|\s+')
_RE_PRUNE = re.compile(r'A-|An-|[\!"#\$%&\'\(\)\*\+\,\./:;<=>\?@\[\\\]\^`\{\|\}~]')
_RE_MULTIPLE = re.compile(r'-+')
_RE_PERMALINK = re.compile(r'(.+?)/+(?!%)')


class Engine(object):

    def __init__(self, config):
        """Initializes the engine.
        """
        if not isinstance(config, SessionConfig):
            raise TypeError("Engine objects must be initialized with SessionConfig object.")

        self.CONFIG = config
        self.units = []

    def globdir(self, directory, pattern='*', iter=False):
        """Returns glob or iglob results for a given directory.
        """
        pattern = os.path.join(directory, pattern)
        if iter:
            return glob.iglob(pattern)
        return glob.glob(pattern)

    def set_unit_paths(self, unit, base_dir, base_url='', index_html=True):
        """Sets the permalink and absolute file path for the given unit.

        Arguments:
        unit: Unit instance whose path and URL are to be set
        base_dir: absolute filesystem path to the output site directory
        base_url: base url to be set for the permalink; defaults to an empty
            string so permalinks are relative
        index_html: boolean indicating output file name;  if False then
            the output file name is the '%s.html' where %s is the last
            string of the unit's permalist

        Output file defaults to 'index' so each unit will be written to
        'index.html' in its path. This allows nice URLs without fiddling
        the .htaccess too much.
        """
        url = [base_url]
        path = [base_dir]

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

    def process_text_units(self, conf):
        """Process the units and fill self.units
        """
        # get absolute paths of content files
        units = []
        content_dir = self.globdir(conf.CONTENT_DIR, iter=True)
        files = (x for x in content_dir if os.path.isfile(x))

        # parse each file and fill self.contents with TextUnit-s
        # also set its URL and absolute file path to be written
        for fname in files:
            units.append(TextUnit(fname, conf))
            # paths and permalinks are not set in TextUnit to facillitate
            # testing; ideally, each xUnit should only be using one Config instance
            self.set_unit_paths(units[-1], self.CONFIG.VOLT.SITE_DIR)

        return units

    def sort_units(self, units, sort_key):
        """Sorts the units in self.units.

        Arguments:
        units: list containing units to sort
        sort_key: field name (string) indicating the key used for sorting;
            if preceeded with  a dash ('-') then sorting is reversed
        """
        reversed = sort_key.startswith('-')
        sort_key = sort_key.strip('-')
        units.sort(key=lambda x: eval('x.' + sort_key), reverse=reversed)

    def chain_units(self, units):
        """Set the 'previous' and 'next' permalink attributes for each unit.

        Arguments:
        units: list containing units to chain

        Using this method, each unit can link to the previous or next one
        according to the sorting order.
        """
        for idx, unit in enumerate(units):
            if idx != 0:
                setattr(unit, 'permalink_prev', self.units[idx-1].permalink)
            if idx != len(self.units) - 1:
                setattr(unit, 'permalink_next', self.units[idx+1].permalink)

    def write_units(self, template_path):
        """Writes single units into its output file.

        Arguments:
        template_path: template file name; must exist in the defined template
            directory
        """
        template_file = os.path.basename(template_path)
        template_env = self.CONFIG.SITE.TEMPLATE_ENV
        template = template_env.get_template(template_file)

        for unit in self.units:
            # warn if files are overwritten
            # this indicates a duplicate post, which could result in
            # unexptected results
            if os.path.exists(unit.path):
                # TODO: find a better exception name
                raise ContentError("'%s' already exists!" % unit.path)
            os.makedirs(os.path.dirname(unit.path))
            with open(unit.path, 'w') as target:
                rendered = template.render(page=unit.__dict__, site=self.CONFIG.SITE)
                self.write_output(target, rendered)

    def write_output(self, file_obj, string):
        """Writes string to the open file object.

        Arguments:
        file_obj: open file object
        string: string to write

        This is written to facillitate testing of the calling method.
        """
        file_obj.write(string.encode('utf8'))

    def process_packs(self):
        """Process the packs and use the results to fill self.packs.
        """
        raise NotImplementedError("Subclasses must implement process_packs().")

    def run(self):
        """Starts the engine processing.
        """
        raise NotImplementedError("Subclasses must implement run().")


class Unit(object):

    def __init__(self, id):
        """Initializes Unit instance.

        Arguments:
        id: any string that refers to the Unit instance exclusively
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

        # raise exception if there are non-ascii chars
        try:
            string.decode('ascii')
        except UnicodeDecodeError:
            raise ContentError("Slug in '%s' contains non-ascii characters." % self.id)

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


class TextUnit(Unit):
    """Class representation of text resources.

    This unit represents resources whose metadata (YAML header) is contained
    in the same file as the content. Some examples of resources like this 
    is a single blog post or a single plain page. 
    """

    def __init__(self, fname, conf, delim=_RE_DELIM):
        """Initializes TextUnit.

        Arguments:
        fname: source filename
        conf: Config object containing unit options
        """
        super(TextUnit, self).__init__(fname)

        with self.open_text(self.id) as source:
            # open file and remove whitespaces
            read = filter(None, delim.split(source.read()))
            # header should be parsed by yaml into dict
            header = self.parse_yaml(read.pop(0))
            if not isinstance(header, dict):
                raise ParseError("Header format unrecognizable in '%s'." \
                        % fname)

            # set blog unit file contents as attributes
            for field in header:
                self.check_protected(field, conf.PROTECTED)
                if field in conf.FIELDS_AS_DATETIME:
                    header[field] = self.as_datetime(\
                            header[field], conf.CONTENT_DATETIME_FORMAT)
                if field in conf.FIELDS_AS_LIST:
                    header[field] = self.as_list(header[field], conf.LIST_SEP)
                if field == 'slug':
                    header[field] = self.slugify(header[field])
                if isinstance(header[field], (int, float)):
                    header[field] = str(header[field])
                setattr(self, field.lower(), header[field])

            self.set_markup(MARKUP)
            # content is everything else after header
            self.content = read.pop(0).strip()

        # check if all required fields are present
        self.check_required(conf.REQUIRED)

        # set other attributes
        # if slug is not set in header, set it now
        if not hasattr(self, 'slug'):
            self.slug = self.slugify(self.title)
        # and set global values
        for field in conf.GLOBAL_FIELDS:
            if not hasattr(self, field):
                setattr(self, field, conf.GLOBAL_FIELDS[field])

        # set permalink components
        self.permalist = self.get_permalist(conf.PERMALINK, conf.URL)
        # set displayed time string
        if hasattr(self, 'time'):
            self.display_time = self.time.strftime(conf.DISPLAY_DATETIME_FORMAT)


class Pack(object):
    """Class for handling Unit objects in packs.

    We might want to use this to handle units togethers, such as when
    we're handling summary pages for blog posts.
    """
    def __init__(self, unit_idxs, pack_idx, site_dir, base_permalist=[], \
            base_url='', last=False, pagination_dir=''):
        """Initializes Pack instance.

        Arguments:
        unit_idxs: list or tuple containing the indexes of Engine.units
            to write. Packs are made according to unit_idxs' sorting order
        pack_idx: index of the pack object relative to to other pack objects.
        site_dir: absolute file path to the output directory
        base_permalist: list of URL components common to all pack permalinks;
        base_url: base url to be set for the permalink; defaults to '' so
            permalinks are relative
        last: boolean indicating whether this pack is the last one
        pagination_dir: directory for paginated items with index > 1
        """
        self.unit_idxs = unit_idxs
        # because page are 1-indexed and lists are 0-indexed
        self.pack_idx = pack_idx + 1
        # this will be appended for pack_idx > 1, e.g. .../page/2
        self.pagination_dir = pagination_dir
        # precautions for empty string, so double '/'s are not introduced
        base_permalist = filter(None, base_permalist)

        if self.pack_idx == 1:
            # if it's the first pack page, use base_permalist only
            self.permalist = base_permalist
        else:
            # otherwise add pagination dir and pack index
            self.permalist = base_permalist + filter(None, [self.pagination_dir,\
                    str(self.pack_idx)])

        # path is path to folder + index.html
        path = [site_dir] + self.permalist + ['index.html']
        self.path = os.path.join(*(path))

        url = [base_url] + self.permalist
        self.permalink = '/'.join(url) + '/'

        # since we can guess the permalink of next and previous pack objects
        # we can set those attributes here (unlike in units)
        pagination_url = [base_url] + base_permalist
        # next permalinks
        if not last:
            self.permalink_next = '/'.join(pagination_url + filter(None, \
                    [self.pagination_dir, str(self.pack_idx + 1)])) + '/'
        # prev permalinks
        if self.pack_idx == 2:
            # if pagination is at 2, previous permalink is to 1
            self.permalink_prev = '/'.join(pagination_url) + '/'
        elif self.pack_idx != 1:
            self.permalink_prev = '/'.join(pagination_url + filter(None, \
                    [self.pagination_dir, str(self.pack_idx - 1)])) + '/'


get_engine = partial(grab_class, cls=Engine)
