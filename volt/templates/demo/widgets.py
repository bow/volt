# Volt custom widgets


def taglist(tags):
    """Jinja2 filter for displaying blog tags."""
    string = '<a href="/tag/%s/" class="button red">%s</a>'
    return ', '.join([string % (tag, tag) for tag in tags])


def latest_posts(units):
    """Widget for showing the latest posts.
    
    Example usage:
        {% for item in widgets.latest_posts %}
            <a href="{{ item.link }}">{{ item.title }}</a>
        {% endfor %}
    
    """
    posts = [(x.title, x.permalink) for x in units][:5]

    results = []
    for title, permalink in posts:
        results.append({'title': title,
                        'link': permalink
                       })
    return results

def monthly_archive(units):
    """Widget for monthly archive.

    Example usage:
        {% for item in widgets.monthly_archive %}
            <a href="{{ item.link }}">{{ item.name }} ({{ item.size }})</a>
        {% endfor %}
    """
    times = set([x.time.strftime("%Y|%m|%B") for x in units])

    results = []
    for timestring in times:
        year, month, month_name = timestring.split("|")
        link = "/blog/%s/%s" % (year, month)
        name = "%s %s" % (month_name, year)
        size = len([x for x in units if \
                x.time.strftime("%Y%m") == '%s%s' % (year, month)])

        results.append({'name': name, 
                        'link': link,
                        'size': size
                       })
    return results
