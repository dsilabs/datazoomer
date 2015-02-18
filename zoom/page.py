
from fill import fill
from request import route
from response import HTMLResponse
from utils import id_for, OrderedSet
from helpers import form_for, link_to, url_for
from tools import as_actions, unisafe
from html import ul
import helpers, tools
from system import system
import os
import log

HEADER_LAYOUT = """
<table id="title_bar"><tr>
<td id="title_bar_left">
<H1>%(title)s</H1>
%(subtitle)s
</td>
<td id="title_bar_right">
%(actions)s
%(search)s
</td>
</tr></table>
"""

class Page(object):
    def __init__(self,content='',callback=None,css=''):

        self.content  = tools.load_content(content) or content
        self.template = system.default_template
        self.callback = callback
        self.css      = css
        self.theme    = system.theme
        self.js       = ''
        self.head     = ''
        self.tail     = ''
        self.title    = ''
        self.subtitle = ''
        self.search   = None
        self.actions  = None
        self.libs     = OrderedSet()
        self.styles   = OrderedSet()


    def render_header(self):

        def render_search(value):
            CLEAR_LAYOUT  = '<span class="clear"><a href="%s"><img src="/static/images/remove_filter.png"></a></span>'
            SEARCH_FIELDS = '<input type="text" class="text_field" id="search_text" name="q" value="%s">%s<input class="search_button" type=submit value="Search">'
            SEARCH_BUTTON = '<input class="search_button" type=submit value="Search">'
            SEARCH_LAYOUT = '<div class="search">%s</div>'

            if value == None:
                return ''
            elif value == '':
                clear = '<span class="clear"></span>'
            else:
                clear = CLEAR_LAYOUT % ('/'.join([''] + route + ['clear']))
            return  SEARCH_LAYOUT % form_for(SEARCH_FIELDS % (value,clear), method='GET')

        def render_actions(items):
            return as_actions(items)

        header_required = self.title or self.subtitle or self.search or self.actions
        if not header_required: return ''
        return unisafe(HEADER_LAYOUT % dict(
                title=self.title,
                subtitle=self.subtitle,
                search=render_search(self.search),
                actions=as_actions(self.actions)))


    def render(self):

        def handle(tag,*args,**keywords):
            if hasattr(self, tag):
                attr = getattr(self, tag)
                if callable(attr):
                    repl = attr(self, *args, **keywords)
                else:
                    repl = attr
                return fill('<dz:','>', repl, handle)

            if tag in helpers.__dict__ and callable(helpers.__dict__[tag]):
                """call functions in a module or module-like object"""
                helper = helpers.__dict__[tag]
                return fill('<dz:','>', helper(*args, **keywords), handle)

        def set_setting(thing, name):
            if thing=='template':
                self.template = name
            elif thing=='app_title':
                self.app_title = name
            return '<!-- %s set to "%s" -->' % (thing, name)

        def render_snippet(system_snippet, page_snippet):
            return '\n'.join(system_snippet | OrderedSet([page_snippet]))

        def render_script_tags(system_scripts, page_scripts):
            scripts = system_scripts | page_scripts
            h = scripts and '\n        <!-- Page Specific Scripts -->\n' or ''
            c = '\n'.join('        <script type="text/javascript" src="{}"></script>'.format(t) for t in scripts)
            t = scripts and '\n\n' or ''
            return h + c + t

        def render_style_sheets(system_style_sheets, page_style_sheets):
            sheets = system_style_sheets | page_style_sheets
            h = sheets and '\n        <!-- Page Specific Styles -->\n' or ''
            c = '\n'.join('        <link rel="stylesheet" type="text/css" href="{}">'.format(t) for t in sheets)
            t = sheets and '\n\n' or ''
            return h + c + t

        DEFAULT_TEMPLATE = os.path.join(system.root,'themes','default','default.html')

        self.content = fill('<dz:set_','>', self.content, set_setting)

        self.styles = render_style_sheets(system.styles, self.styles)
        self.css    = render_snippet(system.css, self.css)
        self.libs   = render_script_tags(system.libs, self.libs)
        self.js     = render_snippet(system.js, self.js)
        self.head   = render_snippet(system.head, self.head)
        self.tail   = render_snippet(system.tail, self.tail)

        if len(route)>1:
            breadcrumb = link_to(system.app.title,'/'+system.app.name)
        else:
            breadcrumb = ''

        template_pathname = system.theme_path 
        if template_pathname:
            template_filename = os.path.join(template_pathname, self.template+'.html')
            if not os.path.exists(template_filename):
                if not self.template in ['index','content']:
                    log.logger.warning('template missing (%s)' % (template_filename))
                template_filename = os.path.join(template_pathname, 'default.html')
        self.tpl = template_pathname and tools.load(template_filename) or tools.load(DEFAULT_TEMPLATE)

        save_content = self.content
        self.content = self.render_header() + self.content
        content = fill('<dz:','>', self.tpl, handle)
        self.content = save_content
        if self.callback:
            content = fill('{{','}}', content, self.callback)

        return HTMLResponse(content)

def render(content='', items=None):
    """Render some content"""
    if items != None:
        content = unisafe(content)
        if hasattr(items,'keys'):
            t = content % items
        else:
            t = ''.join(content % item for item in items)
    else:
        t = content
    return unisafe(t)

def page(content='', template=None, callback=None, css='', js='', title='', subtitle='', search=None, actions=None, items=None, head=''):

    system.result = page = Page()

    page.css = css
    page.js = js
    page.title = title
    page.subtitle = subtitle
    page.search  = search
    page.actions = actions
    page.callback = callback
    page.template = template or system.default_template
    page.head = head

    page.content = render(content, items)

    return page


