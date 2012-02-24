# Volt base engine

import codecs
import glob
import os
import re
from collections import OrderedDict
from datetime import datetime

from volt import ConfigError, ContentError, ParseError
from volt.config import config


MARKUP = { '.html': 'html',
           '.md': 'markdown',
           '.markdown': 'markdown',
         }


class BaseEngine(object):

    def __init__(self, unit_class=None):
        """Initializes the engine

        Arguments:
        content_container: content container class subclassing BaseUnit
        """
        if not issubclass(unit_class, BaseUnit):
            raise TypeError("Engine must be initialized with a content container class.")

        self.unit_class = unit_class
        self.units = OrderedDict()

    def globdir(self, directory, pattern='*', iter=False):
        """Returns glob or iglob results for a given directory.
        """
        pattern = os.path.join(directory, pattern)
        if iter:
            return glob.iglob(pattern)
        return glob.glob(pattern)

    def parse(self):
        """Parses the content, returning BaseUnit object.
        """
        raise NotImplementedError("Subclasses must implement parse().")

    def create_dirs(self):
        """Creates all required directories in the site folder.
        """
        raise NotImplementedError("Subclasses must implement create_dirs().")

    def build_paths(self):
        """Builds all the required URLs.
        """
        raise NotImplementedError("Subclasses must implement build_paths().")

    def write_single(self):
        """Writes a single BaseUnit object to an output file.
        """
        raise NotImplementedError("Subclasses must implement write_single().")

    def write_multiple(self):
        """Writes an output file composed of multipe BaseUnit object.
        """
        raise NotImplementedError("Subclasses must implement write_multiple().")

    def run(self):
        """Starts the engine processing.
        """
        raise NotImplementedError("Subclasses must implement run().")


class BaseUnit(object):

    def open_text(self, fname, mod='r', enc='utf-8'):
        """Open text files with Unicode encoding.

        Arguments:
        fname: file name to open
        mod: file mode
        enc: file encoding
        """
        return codecs.open(fname, mode=mod, encoding=enc)

    def check_protected(self, prot, header):
        """Check if none of the defined header fields are in the protected list.
        
        Arguments:
        prot: iterable that contains protected header fields
        header: dictionary resulting from header parsing
        """
        for field in prot:
            if prot in header:
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

    def process_into_list(self, fields, sep):
        """Transforms a comma-separated tags or categories string into a list.

        Arguments:
        fields: list of fields to transform into list
        sep: field subitem separator
        """
        for field in fields:
            if hasattr(self, field):
                setattr(self, field, filter(None, \
                        getattr(self, field).strip().split(sep)))

    def process_time(self, fmt):
        """Transforms time string into a datetime object.

        Arguments:
        fmt: time format string
        """
        if hasattr(self, 'time'):
            str_time = getattr(self, 'time')
            setattr(self, 'time', datetime.strptime(str_time, fmt))

    def get_markup(self, markup_dict):
        """Sets the markup language into a header key-value pair.

        Arguments:
        markup_dict: dictionary with file extensions as keys and
            their corresponding markup language as values
        """
        if not hasattr(self, 'markup'):
            ext = os.path.splitext(self.id)[1]
            try:
                setattr(self, 'markup', markup_dict[ext])
            except:
                setattr(self, 'markup', 'html')
        setattr(self, 'markup', getattr(self, 'markup').lower())
        if getattr(self, 'markup') not in markup_dict.values():
            raise ContentError("Markup language '%s' is not supported." % \
                    getattr(self, 'markup'))

    def set_slug(self, string):
        """Transforms the given string into a slug and set it as a slug instance attribute.

        Arguments:
        string: string to transform into slug
        """
        string = string.strip()

        # remove english articles
        string = re.sub('A\s|An\s', '', string)

        # replace spaces, etc with dash
        string = re.sub(r'\s([A|a]n??)\s|_|\s+', '-', string)

        # remove bad chars
        bad_chars = r'[\!"#\$%&\'\(\)\*\+\,\./:;<=>\?@\[\\\]\^`\{\|\}~]'
        string = re.sub(bad_chars, '', string)
        # warn if there are non-ascii chars
        assert string.decode('utf8') == string

        # slug should not begin or end with dash or contain multiple dashes
        string = re.sub(r'^-+|-+$', '', string)
        string = re.sub(r'-+', '-', string)

        # raise exception if slug results in an empty string
        if not string:
            raise ContentError("Slug for '%s' is an empty string." % self.id)

        setattr(self, 'slug', string.lower())

    def set_permalink(self, pattern, base_url=''):
        """Sets permalink according to pattern

        Arguments:
        pattern: string replacement pattern
        base_url: string that will be appended in front of the permalink

        The pattern argument may refer to the current object's attributes by
        enclosing them in square brackets. If the instance attribute is a
        datetime object, it must be formatted by specifying a string format
        argument.

        Here are several examples of a valid permalink pattern:
        - '{time:%Y/%m/%d}/{slug}'
        - '{time:%Y}/post/{time:%d}/blog/{id}'
        """
        # raise exception if there are spaces?
        if pattern != re.sub(r'\s', '', pattern):
            raise ContentError("Permalink in '%s' contains whitespace(s)." \
                    % self.id)
        
        # strip preceeding '/' but make sure ends with '/'
        pattern = re.sub(r'^/+', '', pattern)
        pattern = re.sub(r'/*$', '/', pattern)

        # get all permalink components and store into list
        perms = filter(None, [base_url]) + re.findall(r'(.+?)/+(?!%)', pattern)

        # process components that are enclosed in {}
        for i in range(len(perms)):
            if perms[i][0] == '{' and perms[i][-1] == '}':
                cmp = perms[i][1:-1]
                if cmp.startswith('time'):
                    if not hasattr(self, cmp[:4]):
                        raise ContentError("'%s' has no '%s' attribute." % \
                                (self.id, cmp[:4]))
                    perms[i] = datetime.strftime(getattr(self, 'time'), cmp[5:])
                else:
                    if not hasattr(self, cmp):
                        raise ContentError("'%s' has no '%s' attribute." % \
                                (self.id, cmp))
                    perms[i] = getattr(self, cmp)

        url = '/'.join(filter(None, perms)).replace(' ', '')
        setattr(self, 'permalink', url)
