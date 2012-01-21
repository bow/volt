import codecs
import os
import re
from datetime import datetime

import yaml


_MARKUP = {
           '.markdown': 'markdown', '.md': 'markdown',
           '.rst': 'rst', '.textile': 'textile',
           '.html': 'html'
          }

_POST_TIME_FORMAT = "%Y/%m/%d %H:%M"


class ParseError(Exception):
    pass

class ContentError(Exception):
    pass


class Content(object):
    """Class that represents a content object in volt.

    At the moment it is only for text content (blog posts, pages).
    Support for other content types (e.g. images) is planned for
    future releases.

    """
    
    def __init__(self, filename):
        """Initializes the Content object.

        Args:
          filename: filename of text content.

        """
        self.filename = filename
        with codecs.open(filename, 'r', 'utf8') as source:
            self._parse_text_content(source)
        if not hasattr(self, 'title') or not hasattr(self, 'time'):
            raise ContentError("Missing 'title' or 'time' in %s(filename)." \
                    % self.filename)
        self.time = self._process_time()
        self.markup = self._get_markup_lang()
        if hasattr(self, 'tags'):
            self.tags = self._process_tags()

    def _parse_text_content(self, source):
        """Parses the content of a text file.

        Header parsing results are stored as Content object attrributes,
        while the rest of the file is stored in self.content.

        Args:
          source: file object that implements read()

        """
        pattern = re.compile(r'^---$', re.MULTILINE)
        parsed = filter(None, pattern.split(source.read()))
        header = yaml.load(parsed.pop(0))
        if not isinstance(header, dict):
            raise ParseError("Header format unrecognizable in %(filename)." \
                    % self.filename)
        for key in header:
            setattr(self, key.lower(), header[key])
        self.content = parsed.pop(0).strip()

    def _get_markup_lang(self):
        """Returns the content markup language.

        Markup language is guessed first and foremost based on the 
        file extension. Failing that, the method checks if the header 
        specifies 'markup'. If no 'markup' is specified or if the 
        specified markup is not implemented, a ParseError exception is raised.

        """
        ext = os.path.splitext(self.filename)[1]
        if ext.lower() in _MARKUP:
            return _MARKUP[ext.lower()]
        else:
            if hasattr(self, 'markup') and \
                    self.markup.lower() in _MARKUP.values():
                return self.markup.lower()
            else:
                raise ParseError("Markup language unknown or unimplemented in \
                        %s(filename)." % self.filename)
    
    def _process_tags(self):
        """Changes self.tags from a string to a list.

        """
        return filter(None, self.tags.split(', '))

    def _process_time(self):
        """Changes self.time from string to a datetime object.

        """
        return datetime.strptime(self.time, _POST_TIME_FORMAT)
