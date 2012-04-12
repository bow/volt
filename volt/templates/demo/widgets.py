# Volt custom widgets


def taglist(tags):
    """Jinja2 filter for displaying blog tags."""
    # html string format for each tag
    format = '<a href="/tag/%s/" class="button red">%s</a>'
    # return a comma-separated html string containing all tags
    return ', '.join([format % (tag, tag) for tag in tags])


def latest_posts(units):
    """Engine widget for showing the latest posts.
    
    Example usage:
        {% for item in widgets.latest_posts %}
            <a href="{{ item.permalink }}">{{ item.title }}</a>
        {% endfor %}
    """
    # get title and permalink of the five most recent posts
    posts = [(x.title, x.permalink) for x in units[:5]]

    # create title, permalink dict for each post
    results = []
    for title, permalink in posts:
        results.append({'title': title,
                        'permalink': permalink
                       })
    return results


def monthly_archive(units):
    """Engine widget for monthly archive.

    Example usage:
        {% for item in widgets.monthly_archive %}
            <a href="{{ item.link }}">{{ item.name }} ({{ item.size }})</a>
        {% endfor %}
    """
    # get string containing time elements to use
    times = set([x.time.strftime("%Y|%m|%B") for x in units])

    # create dicts containing year, month number (for constructing links)
    # and the month name (for display on the page)
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


def github_search():
    """Site widget for returning github repo search, sorted on last push time.
    
    Example usage:
        {% for item in widgets.github_search %}
            <a href="{{ item.url }}">{{ item.name }} ({{ item.watchers }})</a>
        {% endfor %}
    """
    import json
    import urllib
    from datetime import datetime
    from volt.utils import console

    # set our search parameters
    query_string = 'static website'
    args = {'language': 'Python'}
    base_url = 'http://github.com/api/v2/json/repos/search/'

    # retrieve search results using urllib and json
    query = '%s%s' % (query_string.replace(' ', '+'), '?' + urllib.urlencode(args))
    try:
        response = urllib.urlopen(base_url + query).read()
    except IOError:
        console("WARNING: github_search can not connect to the internet.\n", \
                color='red', is_bright=True)
        return []
    data = json.loads(response)['repositories']

    # get repos with at least 10 watchers
    results = [repo for repo in data if repo['watchers'] >= 10]

    # finally, we'll sort our selection ~ most recent push time first
    def gettime(datestr, format="%Y/%m/%d %H:%M:%S"):
        return datetime.strptime(datestr[:-6], format)
    results.sort(key=lambda x: gettime(x['pushed_at']), reverse=True)

    return results
