# Volt plugin for markdown

try:
    import discount
    DISCOUNT = True
except ImportError:
    import markdown
    DISCOUNT = False

from volt.plugin import Processor


class Markdown(Processor):
    """Processor plugin for transforming markdown syntax to html.
    """
    def process(self, units):
        for unit in units:
            if getattr(unit, 'markup') == 'markdown':
                string = getattr(unit, 'content')
                string = self.get_markdown(string)
                setattr(unit, 'content', string)

    def get_markdown(string):
        """Returns html string of a markdown content.

        Arguments:
        string: string to mark
        """
        if DISCOUNT:
            marked = discount.Markdown(string.encode('utf8'))
            html = marked.get_html_content()
            return html.decode('utf8')

        return markdown.markdown(string)
