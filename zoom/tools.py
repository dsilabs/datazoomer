# Copyright (c) 2005,2006,2007 Dynamic Solutions Inc. (support@dynamic-solutions.com)
#
# This file is part of DataZoomer.
#
# DataZoomer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DataZoomer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""General purpose tools"""

import os
import datetime
from markdown import Markdown 
from system import system
from request import request, route
from response import HTMLResponse, RedirectResponse
from utils import id_for
from html import ul, div

# Handy date values
today     = datetime.date.today()
one_day   = datetime.timedelta(1)
one_week  = one_day * 7
one_hour  = datetime.timedelta(hours=1)
one_minute= datetime.timedelta(minutes=1)
yesterday = today - one_day
tomorrow  = today + one_day
now       = datetime.datetime.now()
first_day_of_the_month = datetime.date(today.year,today.month,1)
last_day_of_last_month = first_day_of_the_month - one_day
first_day_of_last_month = datetime.date(last_day_of_last_month.year,last_day_of_last_month.month,1)
last_month = (first_day_of_last_month,last_day_of_last_month)
#me        = zoomer.user_id
# one_year, one_hour, one_month, ago, ahead

class DB(object):
    """Convenient system database access"""
    def __call__(self, cmd, *a, **k):
        return system.database(cmd, *a, **k)
    def __getattr__(self, name):
        return getattr(system.database, name)
db = DB()

def site_url():
    if request.port=='443':
        protocol = 'https'
    else:
        protocol = 'http'
    host = request.server
    port = (request.port not in ['80','443']) and (':%s'%request.port) or ''
    url = '%s://%s%s' % (protocol,host,port)
    return url

def redirect_to(location):
    """Return a redirect response for a URL."""
    if location.startswith('http://'):
        url = location
    else:
        if request.port=='443':
            protocol = 'https'
        else:
            protocol = 'http'
        host = request.server
        uri = '/'.join(request.uri.split('/')[:-1])
        port = (request.port not in ['80','443']) and (':%s'%request.port) or ''
        if location[0]=='/':
            url = '%s://%s%s%s' % (protocol,host,port,location)
        else:
            url = '%s://%s%s/%s/%s' % (protocol,host,port,uri,location)
    return RedirectResponse(url)

def to_page(name=None, *a, **k):
    if name:
        return redirect_to('/%s/%s' % (system.app.name,name), *a, **k)
    else:
        return redirect_to('/%s' % system.app.name, **k)

def as_actions(items):
    """
        returns actions

        >>> as_actions(['New'])
        '<div class="actions"><ul><li><a class="action" id="new-action" href="/new">New</a></li></ul></div>'
        >>> as_actions(['New','Delete'])
        '<div class="actions"><ul><li><a class="action" id="delete-action" href="/delete">Delete</a></li><li><a class="action" id="new-action" href="/new">New</a></li></ul></div>'

    """
    if not items:
        return ''
    result = []
    for item in reversed(items):
        if hasattr(item, '__iter__'):
            if len(item) == 2:
                text, url = item
            else:
                #TODO:  review to see if this is even useful
                text = item[0]
                url = '/'.join([''] + route + [item[1]])
        else:
            text = item
            url = '/'.join([''] + route + [id_for(item)])

        result.append('<a class="action" id="%s-action" href="%s">%s</a>' % (id_for(text), url, text))
    return div(ul(result), Class='actions')

def redirect_to_app(name):
    """Return a redirect response for an app."""
    return RedirectResponse(url_for(name))

def home(view=None):
    """
    Redirect to application home.

        >>> route.append('contact')
        >>> route.append('new')
        >>> route
        ['contact', 'new']
        >>> request.port = '80'
        >>> home().content
        ''
        >>> home().headers
        {'Location': 'http://localhost/contact'}

        >>> home('old').headers
        {'Location': 'http://localhost/contact/old'}

        >>> request.port = '443'
        >>> home('secure').headers
        {'Location': 'https://localhost/contact/secure'}

    """
    if view:
        return redirect_to('/'+route[0]+'/' + view)
    return redirect_to('/'+route[0])

def load(filename):
    """
        Load a file from the application directory into memory.
    """
    pathname = os.path.join(system.app.dir, filename)
    if not os.path.exists(pathname):
        return ''
    else:
        f = open(pathname,'rb')
        t = f.read()
        f.close()
        return t

def load_template(name, default=None):
    """
    Load a template from the theme folder.

    Templates usually have .HTML file extensions and this module
    will assume that's what is desired unless otherwise specified.
    """

    def find_template(name):
        for path in system.templates_paths:
            if os.path.exists(path) and (name in os.listdir(path)):
                return os.path.join(path, name)
        name_lower = name.lower()
        for path in system.templates_paths:
            if os.path.exists(path):
                for filename in os.listdir(path):
                    if filename.lower() == name_lower:
                        return os.path.join(path, filename)

    def load_template_file(name, default):

        pathname = find_template(name)
        if pathname:
            if os.path.exists(pathname):

                f = open(pathname,'r')
                t = f.read()
                f.close()

                if system.theme_comments == 'path':
                    source = filename
                elif system.theme_comments == 'name':
                    source = name[:-5]
                else:
                    source = None

                if source and pathname[-5:].lower() == '.html':
                    result = '\n<!-- source: %s -->\n%s\n<!-- end source: %s -->\n' % (source, t, source)
                else:
                    result = t
                return result

        return default or ''

    if not '.' in name:
        name = name + '.html'
    if '/' in name or '\\' in name:
        raise Exception('Unable to use specified template path.  Templates are located in theme folders.')

    return system.templates.setdefault(name, load_template_file(name, default))


def load_content(name):
    """Load content and apply markdown transformation."""
    import codecs
    if os.path.isfile(name):
        text = codecs.open('%s'%name, mode="r", encoding="utf8").read()
        return markdown(text)
    elif os.path.isfile(name+'.html'):
        text = codecs.open('%s.html'%name, mode="r", encoding="utf8").read()
        return text
    elif os.path.isfile(name+'.md'):
        text = codecs.open('%s.md'%name, mode="r", encoding="utf8").read()
        return markdown(text)
    elif os.path.isfile(name+'.txt'):
        text = codecs.open('%s.txt'%name, mode="r", encoding="utf8").read()
        return markdown(text)
        
def get_menu(name='main'):
    filename = os.path.join(system.config.site_path, 'menus.py')
    if os.path.exists(filename):
        import imp
        src = imp.load_source('menus',filename)
        if hasattr(src,name):
            menu = getattr(src,name)
            if menu:
                return menu
    else:
        filename = os.path.join(system.lib_path, '../../sites/localhost/menus.py')
        if os.path.exists(filename):
            import imp
            src = imp.load_source('menus',filename)
            if hasattr(src,name):
                menu = getattr(src,name)
                if menu:
                    return menu
    return []

def get_setting(name):
    filename = os.path.join(system.config.site_path,'settings.py')
    if os.path.exists(filename):
        import imp
        src = imp.load_source('settings',filename)
        if hasattr(src,name):
            item = getattr(src,name)
            if item != None:
                return item

def how_long(t1,t2):
    """
    Returns a string that describes the difference between two dates.

    >>> how_long(now, now + 2 * one_day)
    '2 days'

    >>> how_long(now, now + 15 * one_day)
    '2 weeks'

    >>> how_long(now, now + 35 * one_day)
    'over a month'

    >>> how_long(now, now + 361 * one_day)
    'almost a year'

    """
    diff = t2 - t1
    if diff.days > 365*2:
        return 'over %s years' % (diff.days / 365)
    elif diff.days > 365*1.75:
        return 'almost two years'
    elif diff.days > 365:
        return 'over a year'
    elif diff.days > 360:
        return 'almost a year'
    elif diff.days > 60:
        return 'over %s months' % (diff.days / 30)
    elif diff.days > 30:
        return 'over a month'
    elif diff.days > 14:
        return '%s weeks' % (diff.days / 7)
    elif diff.days > 1:
        return '%s days' % diff.days
    elif diff.days == 1:
        return '1 day'
    elif diff.seconds > 3600:
        return '%s hours' % int(diff.seconds / 3600)
    elif diff.seconds > 60:
        return '%s minutes' % int(diff.seconds / 60)
    elif diff.seconds > 0:
        return '%s seconds' % int(diff.seconds)
    else:
        return 'a moment'

def how_long_ago(dt):
    """
    Returns a string that describes the difference between a date and today.

    >>> how_long_ago(datetime.datetime.now() - datetime.timedelta(1) * 2)
    '2 days ago'

    """
    if type(dt)==datetime.date:
        d = datetime.datetime(dt.year,dt.month,dt.day)
        diff = datetime.datetime.now() - d
    elif type(dt)==datetime.datetime:
        diff = datetime.datetime.now() - dt
    elif dt == None:
        return None
    else:
        diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(dt)

    if diff.days > 365*2:
        return 'over %s years ago' % (diff.days / 365)
    elif diff.days > 365*1.75:
        return 'almost two years ago'
    elif diff.days > 365:
        return 'over a year ago'
    elif diff.days > 360:
        return 'almost a year ago'
    elif diff.days > 60:
        return 'over %s months ago' % (diff.days / 30)
    elif diff.days > 30:
        return 'over a month ago'
    elif diff.days > 14:
        return '%s weeks ago' % (diff.days / 7)
    elif diff.days > 1:
        return '%s days ago' % diff.days
    elif diff.days == 1:
        return 'yesterday'
    elif diff.seconds > 3600:
        return '%s hours ago' % int(diff.seconds / 3600)
    elif diff.seconds > 60:
        return '%s minutes ago' % int(diff.seconds / 60)
    elif diff.seconds > 0:
        return '%s seconds ago' % int(diff.seconds)
    else:
        return 'a moment ago'

def htmlquote(text):
    r"""
    Encodes `text` for raw use in HTML.

        >>> htmlquote(u"<'&\">")
        u'&lt;&#39;&amp;&quot;&gt;'
    """
    text = text.replace(u"&", u"&amp;") # Must be done first!
    text = text.replace(u"<", u"&lt;")
    text = text.replace(u">", u"&gt;")
    text = text.replace(u"'", u"&#39;")
    text = text.replace(u'"', u"&quot;")
    return text

def unisafe(val):
    if val is None:
            return u''
    elif isinstance(val, str):
        try:
            val = val.decode('utf-8')
        except:
            val = val.decode('Latin-1')
    elif not isinstance(val, unicode):
        val = unicode(val)
    return val

def websafe(val):
    return htmlquote(unisafe(val))

def markdown(content):
    def make_page_name(text):
        result = []
        for c in text.lower():
            if c in 'abcdefghijklmnopqrstuvwxyz01234567890.-/':
                result.append(c)
            elif c == ' ':
                result.append('-')
        text = ''.join(result)
        if text.endswith('.html'):
            text = text[:-5]
        return text

    def url_builder(label,base,end):
        return make_page_name(label) + '.html'

    extras = ['tables','def_list','wikilinks','toc']
    configs = {'wikilinks':[('build_url',url_builder)]}
    md = Markdown(extensions=extras,extension_configs=configs)
    return md.convert(unisafe(content))


if __name__=='__main__':

    import unittest
    import doctest

    doctest.testmod()

    class Tests(unittest.TestCase):
        def test_how_long_ago(self):
            pass
            
        def test_how_long(self):
            from datetime import datetime
            self.assertEqual(how_long(datetime(2010,10,1),datetime(2010,10,7)),'6 days')
            self.assertEqual(how_long(datetime(2010,10,1),datetime(2010,10,8)),'7 days')
            self.assertEqual(how_long(datetime(2010,10,1),datetime(2010,10,9)),'8 days')
            self.assertEqual(how_long(datetime(2010,10,1),datetime(2010,10,16)),'2 weeks')
            
    unittest.main()



















