"""DataZoomer Helpers"""
import os
from system import system
from manager import manager
import tools
from request import request, route
from user import user
import html
from zoom.utils import *
import flags
from snippets import snippet
import goals
from urllib import quote
from string import ascii_letters, digits

APP_MENU_LENGTH = 5

def elapsed(fmt='%f'):
    """Returns time it took to generate current page."""
    return fmt % system.elapsed_time

def warning(*text):
    """Adds one or more warnings to list of warnings to be displayed on next generated page."""
    if not system.session.system_warnings:
        system.session.system_warnings = []
    for item in text:
        system.session.system_warnings.append(item)

def error(*text):
    """Adds one or more errors to list of errors to be displayed on next generated page."""
    if not system.session.system_errors:
        system.session.system_errors = []
    for item in text:
        system.session.system_errors.append(item)

def message(*text):
    """Adds one or more messages to list of messages to be displayed on next generated page."""
    if not system.session.system_messages:
        system.session.system_messages = []
    for item in text:
        system.session.system_messages.append(item)

def warnings():
    """Returns an unordered list of warnings in HTML and clears the warning list."""
    result = system.session.system_warnings and html.ul(system.session.system_warnings) or ''
    system.session.system_warnings = []
    return result

def errors():
    """Returns an unordered list of errors in HTML and clears the errors list."""
    result = system.session.system_errors and html.ul(system.session.system_errors) or ''
    system.session.system_errors = []
    return result

def messages():
    """Returns an unordered list of messages in HTML and clears the messages list."""
    result = system.session.system_messages and html.ul(system.session.system_messages) or ''
    system.session.system_messages = []
    return result

def alerts():
    """Returns unordered lists of warnings, errors and messages in HTML and clears those lists."""
    return warnings() + errors() + messages()

def tracker():
    """Returns Google Analytics tracker code for the site (set ID in site.conf)."""
    if system.site.tracking_id:
        tpl = """
        <script>
          (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
          (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
          m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
          })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

          ga('create', '%s', 'auto');
          ga('send', 'pageview');

        </script>
        """
        return tpl % system.site.tracking_id
    return ''

def set_template(name):
    """Allows user to specify an alternate theme template for rendering.
    This is most commonly used in the content of the index page of a site to
    specify a special template for the front page of a site.

    Renders as an empty string.
    """
    # The logic for the tag corresponding to this helper is found in the page
    # module.  It's implemented here as a helper as well so that when the template
    # is rendered on it's final pass it is invisible.
    return ''

def theme():
    """Returns the system theme name."""
    return system.theme

def protocol():
    return request.protocol

def include(name):
    """Includes another template into the current template."""
    return tools.load_template(name)

def printed_output():
    """Returns the printed output for debugging."""
    return '{*PRINTED*}'

def system_menu_items():
    """Returns the system menu."""
    def title_of(app):
        return manager.apps[app].title

    _dropdown = html.li([link_to(title_of(app),'/'+app) for app in manager.get_system_app_names() if manager.apps[app].visible])
    return """
        <div class="navbar-collapse collapse">
            <div class="dropdown user-info navbar-right">
                <span class="dropdown-toggle" style="cursor:pointer;" type="button" id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                %s
                <span class="caret"></span>
                      </span>
                      <ul class="dropdown-menu">
                        %s
                      </ul>
                    </div>
        """ %(user.username.title(), _dropdown)

def system_menu():
    """Returns the system menu."""
    return '<li>%s</li>' % system_menu_items()

def main_menu_items():
    """Returns the main menu."""

    def assign_defaults(name,title,url,group=[]):
        return (name,title,url,group)

    links = []
    visible_items = []
    static_links = [assign_defaults(*item) for item in tools.get_menu()]

    for (name,title,url,group) in static_links:
        if group==[] or [item for item in group if item in user.groups]:
            if manager.get_app(name) and not manager.get_app(name).visible: continue
            selector = (len(route)>1 and route[0]=='content' and route[1]==name or len(route) and route[0]==name) and ' id="current"' or ''
            bootstrap_selector = (len(route)>1 and route[0]=='content' and route[1]==name or len(route) and route[0]==name) and ' class="active"' or ''
            links.append('<li%s><a href="%s"%s>%s</a></li>' % (bootstrap_selector,url_for(url), selector, title))
            visible_items.append(name)

    visible_items.extend(['content','login'])

    if user.is_developer:
        current_app = route[0]
        if not current_app in visible_items:
            if visible_items[0] in ['index','home']:
                pos = 1
            else:
                pos = 0
            url = '<li class="active"><a href="%s" id="current">%s</a></li>' % (url_for('/'+current_app),system.app.title)
            links.insert(pos, url)

    return ''.join(links)

def main_menu():
    """Returns the main menu."""
    return '<ul>%s</ul>' % main_menu_items()

def _app_menu_items(uri, route, items):

    def url_for(*a, **k):
        return construct_url(uri, route, a, k)

    def as_menu_item(n, item):
        if type(item) in [str, unicode]:
            name = n and id_for(item) or ''
            return name or 'index', item, name
        else:
            if len(item) == 2:
                return item[1], item[0], item[1]
            elif len(item) == 3:
                return item
            else:
                raise Exception('unkown menu item {}'.format(repr(item),))

    def as_menu(items):
        for n, item in enumerate(items):
            yield as_menu_item(n, item)

    links = []
    selected = \
        len(route)>2 and route[0]=='content' and route[2] or \
        len(route)>1 and route[1] or \
        len(route) == 1 and route[0]!='content' and 'index'
    for name, title, url in as_menu(items):
        if url == '':
            url = url_for('/'+route[0])
        elif url[0]=='/':
            url = url_for(url)
        else:
            url = url_for('/'+route[0]+'/'+url)
        selector = name==selected and ' id="current"' or ''
        bootstrap_selector = name==selected and ' class="active"' or ''
        links.append('<li%s><a href="%s"%s>%s</a></li>' % (
            bootstrap_selector,
            url,
            selector,
            title,
            ))
    return links

def app_title():
    return system.app.title

def _app_menu(uri, route, items):
    """construct app menu

    >>> items = [
    ...     ('index','Overview','index'),
    ...     ('system-log','System Log','system-log'),
    ...     ('errors','Errors','errors'),
    ...     ('top-users','Top Users','top-users'),
    ...     ('addresses','Addresses','addresses'),
    ...     ('tables','Tables','tables'),
    ...     ('environment','Environment','environment'),
    ...     ('python','Python','python'),
    ...     ]
    >>> t = _app_menu('', ['info'], items)
    >>> s = ''.join([
    ...     '<ul><li class="active"><a href="/info/index" id="current">Overview</a></li>',
    ...     '<li><a href="/info/system-log">System Log</a></li>',
    ...     '<li><a href="/info/errors">Errors</a></li>',
    ...     '<li><a href="/info/top-users">Top Users</a></li>',
    ...     '<li><a href="/info/addresses">Addresses</a></li>',
    ...     '<li><a href="/info/tables">Tables</a></li>',
    ...     '<li><a href="/info/environment">Environment</a></li>',
    ...     '<li><a href="/info/python">Python</a></li></ul>',
    ...     ])
    >>> t == s
    True

    >>> items = 'Overview','Page One'
    >>> t = _app_menu('', ['info'], items)
    >>> s = ''.join(['<ul><li class="active"><a href="/info" id="current">Overview</a></li>',
    ...              '<li><a href="/info/page-one">Page One</a></li></ul>'])
    >>> t == s
    True

    >>> items = 'Overview','Page One'
    >>> t = _app_menu('', ['info','page-one'], items)
    >>> s = ''.join(['<ul><li><a href="/info">Overview</a></li>',
    ...              '<li class="active"><a href="/info/page-one" id="current">',
    ...              'Page One</a></li></ul>'])
    >>> t == s or r'{}!={}'.format(repr(t),repr(s))
    True

    """
    app_menu_size = system.app.app_menu_size
    menu_items = _app_menu_items(uri, route, items)
    app_dropdown_list = ''.join(['<li>'] + menu_items + ['</li>'])
    if len(menu_items) <= app_menu_size:
        return ''.join(['<ul>'] + menu_items + ['</ul>'])
    elif len(menu_items) > app_menu_size:
        return """
            <div class="dropdown">
                <button class="dropdown-toggle" type="button" id="app-menu-dropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                    <h4>%s <span class="caret"></span></h4>
                </button>
                <ul class="dropdown-menu">
                    %s
                </ul>
            </div>
            """ %(system.app.name.title(), app_dropdown_list)
    else:
        return ''


def app_menu_items():
    """Returns the app menu items."""
    items = getattr(system.app, 'menu', [])
    return ''.join(_app_menu_items(system.uri, route, items))

def app_menu():
    """Returns the app menu."""
    items = getattr(system.app, 'menu', [])
    return _app_menu(system.uri, route, items)

def app_classed():
    """ Return the application title in a form for an HTML class attribute"""
    return attribute_escape(id_for(system.app.title))

def app_side_nav(default='no apps'):

    if user.username == system.guest: return ''

    head_tpl = """
        <nav class="navbar-side " role="navigation">
            <div class="navbar-collapse sidebar-collapse collapse">
                <ul id="side" class="nav navbar-nav side-nav">
    """

    tail_tpl = """
                </ul>
                <!-- /.side-nav -->
            </div>
            <!-- /.navbar-collapse -->
        </nav>
        <!-- end side navbar -->
    """

    search_tpl = """
                   <!-- begin SIDE NAV SEARCH -->
                    <li class="nav-search">
                        <form role="form">
                            <input type="search" class="form-control" placeholder="Search...">
                            <button class="btn">
                                <i class="fa fa-search"></i>
                            </button>
                        </form>
                    </li>
                    <!-- end SIDE NAV SEARCH -->
    """

    dash_tpl = """
                    <!-- begin DASHBOARD LINK -->
                    <li>
                        <a %(active)s href="/dashboard">
                            <i class="fa fa-dashboard"></i> Dashboard
                        </a>
                    </li>
                    <!-- end DASHBOARD LINK -->
    """

    link_tpl = """
                    <!-- begin %(name)s LINK -->
                    <li>
                        <a class="active" href="%(url)s">
                            <i class="fa %(fa_icon)s"></i> %(label)s
                        </a>
                    </li>
                    <!-- end %(name)s LINK -->
    """

    panel_tpl = """
                    <!-- begin %(name)s DROPDOWN -->
                    <li class="panel">
                        <a href="javascript:;" data-parent="#side" data-toggle="collapse" class="accordion-toggle" data-target="#%(id)s">
                            <i class="fa %(fa_icon)s"></i> %(label)s <i class="fa fa-caret-down"></i>
                        </a>
                        <ul class="collapse nav %(expand)s" id="%(id)s">
                            %(items)s
                        </ul>
                    </li>
                    <!-- end %(name)s DROPDOWN -->

    """

    item_tpl = """
                            <li>
                                <a %(active)s href="%(url)s">
                                    <i class="fa %(fa_icon)s"></i> %(label)s
                                </a>
                            </li>
    """

    result = [head_tpl]

    MISC = 'Miscellaneous'

    apps = list(a for a in manager.apps.values() if a.visible and a.name in user.apps)
    categories = sorted(set([MISC] + [i for s in [a.categories for a in apps] for i in s]))

    if 'dashboard' in [a.name for a in apps]:
        result.append(dash_tpl %
                dict(
                    active=route[0]=='dashboard' and 'class="active"' or ''
                    ))

    category_apps = {}
    for app in apps:
        app_categories = app.categories or [MISC]
        for category in app_categories:
            category_apps.setdefault(category, []).append(dict(
                url = '/' + app.name,
                fa_icon = 'fa-chart',
                label = app.title,
                active = app.name != 'home' and app.name == route[0] and 'class="active"' or '',
                ))
            category_apps[category].sort(key=lambda a: a['label'])

    items = []
    for c in sorted(category_apps):
        expand = any(bool(app['active']) for app in category_apps[c]) and 'in' or ''
        items.append(dict(
            fa_icon = '', #'fa-dashboard',
            name = c.upper(),
            label = c,
            url = url_for(c),
            id = id_for(c),
            items = ''.join(item_tpl % app for app in category_apps[c]),
            expand = expand,
            ))

    system.js.add("""
      $(function() {
          $( "#side" ).sortable();
      });

    """)

    result.extend(panel_tpl % i for i in items)
    result.append(tail_tpl)
    return '\n'.join(result)

def h(html_code):
    """Returns HTML with less than and greater than characters converted so it can be rendered as displayable content."""
    return html_code.replace('<','&lt;').replace('>','&gt')

def attribute_escape(untrusted):
    """Attributes escape 'untrusted' before inserting into HTML common attributes

    ** important ** this should not be used for complex attributes, href, src, style
    or event handlers - use "js_escape" instead

        >>> attribute_escape('hello')
        'hello'
        >>> attribute_escape('hello123GOOd')
        'hello123GOOd'
        >>> attribute_escape('hello "> <script>')
        'hello&#x20;&#x22;&#x3e;&#x20;&#x3c;script&#x3e;'
    """
    def __enc(char):
        return '&#x%(encoded)s;' % {'encoded': char.encode("hex")}
    safe = ascii_letters + digits
    return ''.join([char in safe and char or __enc(char) for char in untrusted])

def title():
    """Returns application title."""
    return ' | '.join(OrderedSet([system.app.title, site_name()]))

def content_page():
    """Returns the content page filename without the extension (used with content pages)"""
    f = route and os.path.splitext(route[-1]) or None
    return f and f[0] or 'content'

def removal_icon(url):
    """Generates a removal icon"""
    return '<span class="removal_icon"><a href="%s"><img class="remove" alt="remove" src="%s/images/remove.png"></a></span>' % (url, theme_uri())

def trash_can(url):
    """Generates a trash can icon"""
    return '<span class="trash_can"><a href="%s"><img class="trash" alt="trash" src="%s/images/trash.png"></a></span>' % (url, theme_uri())

def description():
    """Return application description."""
    return system.app.description

def keywords():
    """Return application keywords."""
    return system.app.keywords

def in_form():
    return hasattr(system,'in_form') and bool(system.in_form)

def name_for(text):
    """Calculates a valid HTML field name given an arbitrary string."""
    result = text.replace('*','').replace(' ','_').strip().upper()
    return result

def achieved(name):
    """Triggers a goal achievement entry"""
    goals.achieved(name, system.subject)
    return ''

def current_date():
    """Returns the current date in text form."""
    return '%s' % tools.today

def date():
    """Returns the current date in text form."""
    return '%s' % tools.today

def year():
    """Returns the current year in text form."""
    return tools.today.strftime('%Y')

def session_id():
    """Returns the session ID."""
    return str(system.session.sid)

def user_id():
    """Returns the user id."""
    return user.user_id

def username():
    """Returns the username."""
    return user.username <> system.guest and user.username or ''

def user_full_name():
    """Returns the username."""
    return ' '.join([user.first_name, user.last_name])

def user_first_name():
    """Returns the user's first name."""
    return user.first_name

def user_last_name():
    """Returns the user's last name."""
    return user.last_name

def login_id():
    """Returns the user login id."""
    return user.login_id

def logout_link():
    """Returns a logout link if the user has access to the logout app."""
    return 'logout' in user.apps and link_to('logout','/logout') or ''

def profile_link(classed="welcome"):
    """Returns an avatar profile link"""
    classed = hasattr(classed, '__iter__') and ' '.join(classed) or classed
    avatar = """
<img src="/profile/avatar" class="hidden" onerror="this.style.display='none'" alt="">

<div class="{}">
    <div>Welcome,</div>
    <div><dz:user_first_name></div>
</div>
    """.format(classed)
    return user.is_authenticated and link_to(avatar,'/profile') or avatar

def upper(text):
    """Returns the given text in upper case."""
    return text.upper()
def site_name():
    """Returns the site name."""
    return system.settings.get('site_name')

def site(option,default=''):
    """Returns the site name."""
    return site_name() or default

def owner_name():
    """Returns the name of the site owner."""
    return system.settings.get('owner_name')

def owner_url():
    """Returns the URL of the site owner."""
    return system.settings.get('owner_url')

def owner_link():
    """Returns a link for the site owner."""
    name = owner_name()
    url = owner_url()
    if url:
        return link_to(name, url)
    email = owner_email()
    if email:
        return tag_for('a', name, href='mailto:%s' % email)
    return name

def mailto(email, name=None):
    name = name or email
    return email and tag_for('a', name, href='mailto:{}'.format(email)) or ''

def owner_email():
    return system.settings.get('owner_email')

def admin_email():
    """Returns the email address of the site owner as defined in the site.conf file."""
    return system.settings.get('admin_email')

def uri():
    """Returns the site URI."""
    return system.uri

def flag(label='', url=None, icon='star', id=None, hint=''):
    def get_flag_state(url, owner, icon):
        return bool(flags.flags.find(url=url, owner=owner, icon=icon))
    url = url or request.uri
    id_attr = id and ('id="%s"'%id) or ''
    state = get_flag_state(url, user.username, icon) and icon+'_on' or ''
    tpl = '<a title="%(hint)s" %(id_attr)s label="%(label)s" url="%(url)s" icon="%(icon)s" class="flag %(icon)s %(state)s">Flag Me!</a>'
    return tpl % locals()

def flag_list(icon='star', n=None):
    links = [f.link for f in flags.flags.find(owner=user.username) if not icon or icon==f.icon]
    if n:
        links = links[:n]
    return html.ul(links)

def load_menu(name=None):
    """renders a menu"""
    if name:
        try:
            items = tools.get_menu(name)
            if not items:
                raise Exception('menu %s empty' % name)
        except:
            error('unable to read menu <b>"%s"</b>' % name)
            items = []
        links = []
        for item in items:
            title = item[0]
            url = item[1]
            groups = item[2]
            if groups==[] or [g for g in groups if g in user.groups]:
                links.append('<a href="%s">%s</a>' % (url_for(url), title))
        return html.ul(links)

def theme_uri():
    """Returns the theme URI."""
    return system.uri+'/themes/'+theme()

def remote_addr():
    """Returns the user ip address."""
    return request.ip

def domain():
    """Returns the host name."""
    return request.domain

def host():
    """Returns the host name."""
    return request.host

def button(label='Submit',name=None):
    """Returns a button."""
    return '<input type=submit value="%(label)s" class="button" name="%(name)s">' % dict(name=name or name_for(label),label=label)

def save_button():
    """Returns a save button."""
    return button(label='Save',name='save_button')

def format_field(label,content,edit=in_form()):
    """Returns field with a label formatted in a standard way."""
    if edit:
        tpl = """<div class="field"><div class="field_label">%(label)s</div><div class="field_edit">%(content)s</div></div>"""
    else:
        tpl = """<div class="field"><div class="field_label">%(label)s</div><div class="field_show">%(content)s</div></div>"""
    return tpl % (dict(label=label,content=content))

def tag_for(tag_text,content='',*args,**keywords):
    """Returns an HTML tag."""
    tag_type = tag_text.lower()
    singles = ''.join([' %s' % arg.lower() for arg in args])
    attribute_text = ''.join([' %s="%s"' % (key.lower(),keywords[key]) for key in keywords])
    if content or tag_type.lower() in ['textarea']:
        return '<%s%s%s>%s</%s>' % (tag_type,singles,attribute_text,content,tag_type)
    else:
        return '<%s%s%s />' % (tag_type,singles,attribute_text)

def link_to(label,*args,**keywords):
    """Returns a link to a URL."""
    return tag_for('a',label,href=url_for(*args,**keywords))

def link_to_page(label, *args, **keywords):
    """Returns a link to a page within the current app."""
    if not args:
        args.append(name_for(label))
    return tag_for('a', label, href=url_for('/' + system.app.name, *args,**keywords))

def cancel(**keywords):
    """Returns a cancel link."""
    return link_to('cancel','/'+route[0],**keywords)

def text_input(name,size='1',default='',*args,**keywords):
    """Returns a text input form element."""
    if not in_form():
        return '{{%s}}' % h(name)
    size = int(size)
    value = keywords.get('value','{{%s}}'%name.upper())
    if size in [1,2]:
        isize = size * 20
        return tag_for('input',Class='text',Type='text',size=isize,maxlength=isize,Name=name,value=value)
    elif size==3:
        return tag_for('textarea',content=value,name=name)
    elif size==4:
        return tag_for('textarea',content=value,name=name,Class=large)

def text_field(label='',*args,**keywords):
    """Returns a text input form field."""
    if 'name' not in keywords:
        keywords['name'] = name_for(label)
    return format_field(label,text_input(*args,**keywords))

def date_field(label='',*args,**keywords):
    """Returns a date input form field."""
    if 'name' not in keywords:
        keywords['name'] = name_for(label)
    return format_field(label,text_input(*args,**keywords))

def phone_field(label='',*args,**keywords):
    """Returns a phone input form field."""
    if 'name' not in keywords:
        keywords['name'] = name_for(label)
    return format_field(label,text_input(*args,**keywords))

def url_input(name,default='',*args,**keywords):
    """Returns a URL input form element."""
    if not in_form():
        return '<a target=_window href="{{%s}}">{{%s}}</a>' % (h(name),h(name))
    else:
        return text_input(name,size=2,default=default,*args,**keywords)

def url_field(label='',*args,**keywords):
    """Returns a URL input form field."""
    if 'name' not in keywords:
        keywords['name'] = name_for(label)
    return format_field(label,url_input(*args,**keywords))

def password_input(name,size='1',default='',*args,**keywords):
    """Returns a password input form element."""
    if not in_form():
        return ''
    size = int(size)
    value = keywords.get('value','{{%s}}'%name.upper())
    if size in [1,2]:
        isize = size * 20
        return tag_for('input',Class='text',Type='password',size=isize,maxlength=isize,Name=name,value=value)

def password_field(label='',*args,**keywords):
    """Returns a password input form field."""
    if 'name' not in keywords:
        keywords['name'] = name_for(label)
    return format_field(label,text_input(*args,**keywords))

def radio_input(name,default='',values=''):
    """Returns a radio input form element."""
    if not in_form():
        return '{{%s}}' % h(name)
    result = []
    for label in values.split(';'):
        value = label
        if label == default:
            result.append('<input type="radio" checked=Y name="%s" value="%s" />%s&nbsp;&nbsp;' % (name,value,label))
        else:
            result.append('<input type="radio" name="%s" value="%s" />%s&nbsp;&nbsp;' % (name,value,label))
    return ''.join(result)

def radio_field(label='',*args,**keywords):
    """Returns a radio input form field."""
    if 'name' not in keywords:
        keywords['name'] = name_for(label)
    return format_field(label,radio_input(*args,**keywords))

def select_input(name,value=None,default='',values=''):
    """Returns a select input form element."""
    result = []
    result.append('<select class=select name="%s">' % name)
    current_value = value or default
    for label in values.split(';'):
        value = label
        if label == current_value:
            result.append('<option selected value="%s">%s</option>' % (value,label))
        else:
            result.append('<option value="%s">%s</option>' % (value,label))
    result.append('</select>')
    return ''.join(result)

def select_field(label='',*args,**keywords):
    """Returns a select input form field."""
    if 'name' not in keywords:
        keywords['name'] = name_for(label)
    return format_field(label,select_input(*args,**keywords))

def csrf_token():
    if not system.session.csrf_token:
        from uuid import uuid4
        system.session.csrf_token = uuid4().hex
    return system.session.csrf_token

def form(action=None, **keywords):
    """Returns a form tag."""
    action = action or request.path
    system.in_form = 1
    esc = attribute_escape
    params = keywords.copy()
    form_name = keywords.get('form_name','dz_form')
    method = keywords.get('method','POST')
    if 'method' in keywords:
        del params['method']
    t = []
    for arg_name in params:
        t.append('\n<input type=hidden name="%s" value="%s">' % (esc(arg_name),esc(params[arg_name])))
    if method == 'POST':
        t.append('\n<input type="hidden" name="csrf_token" value="%s">' % csrf_token())
    return '<form action="%s" id="%s" name="%s" method="%s">%s' % (esc(action),esc(form_name),esc(form_name),esc(method),''.join(t))

def form_for(content,**keywords):
    """Returns a form tag with a closing tag, surrounding specified content."""
    return '%s%s</form>'%(form(**keywords),content)

def multipart_form(action='/'+'/'.join(route),*args,**keywords):
    """Returns a multipart form tag."""
    esc = attribute_escape
    params = keywords.copy()
    form_name = keywords.get('form_name','dz_form')
    t = []
    for arg_name in params:
        t.append('\n<input type=hidden name="%s" value="%s">' % (esc(arg_name),esc(params[arg_name])))
    t.append('\n<input type="hidden" name="csrf_token" value="%s">' % csrf_token())
    return '<form action="%s" id="%s" name="%s" method=POST enctype="multipart/form-data">%s\n' % (esc(action),esc(form_name),esc(form_name),''.join(t))

def multipart_form_for(content,**keywords):
    """Returns a multipart form tag with a closing tag, surrounding specified content."""
    return '%s%s</form>'%(multipart_form(**keywords),content)

def construct_url(root,route,a,k):
    """Construct a site URL

    >>> construct_url('',[],[],{})
    ''
    >>> construct_url('/',[],[],{})
    '/'
    >>> construct_url('/data',[],[],{})
    '/data'

    >>> construct_url('',['home'],[],{})
    '/home'
    >>> construct_url('/',['home'],[],{})
    '//home'
    >>> construct_url('/data',['home'],[],{})
    '/data/home'

    >>> construct_url('',['home','alone'],[],{})
    '/home'
    >>> construct_url('/',['home','alone'],[],{})
    '//home'
    >>> construct_url('/data',['home','alone'],[],{})
    '/data/home'

    >>> construct_url('',['home','alone','one'],[],{})
    '/home/alone'
    >>> construct_url('/',['home','alone','one'],[],{})
    '//home/alone'
    >>> construct_url('/data',['home','alone','one'],[],{})
    '/data/home/alone'

    >>> construct_url('',['home','alone','one'],['two'],{})
    '/home/alone/two'
    >>> construct_url('',['home','alone','one'],['two'],{'q':1})
    '/home/alone/two?q=1'
    >>> construct_url('',['home','alone','one'],['two','three'],{'q':1})
    '/home/alone/two/three?q=1'

    """
    a = [str(i) for i in a]
    if a and a[0][0]=='/':
        if len(a[0])>1:
            uri = root + '/'.join(list(a))
        elif root:
            uri = root #+ '/'#.join(list(a)[1:])
        else:
            uri = '/'
    elif a and (a[0].startswith('http://') or a[0].startswith('https://')):
        uri = a[0]
    else:
        uri = '/'.join([root] + list(route[:1]+route[1:-1]) + list(a))

    if k:
        params = '&'.join([quote('%s=%s' % (name,k[name]),safe='/=') for name in k])
        return '%s?%s' % (uri,params)
    else:
        return uri

def url_for(*a, **k):
    """
    Return a URL for a page.

        >>> system.uri = 'http://localhost'
        >>> url_for('test')
        'http://localhost/test'

        >>> system.uri = 'https://localhost'
        >>> url_for('test')
        'https://localhost/test'

        >>> system.uri = 'http://localhost'
        >>> url_for('test',status='"><script>alert(2)</script>')
        'http://localhost/test?status=%22%3E%3Cscript%3Ealert%282%29%3C/script%3E'

        >>> system.uri = 'http://localhost'
        >>> route.append('main')
        >>> url_for('test')
        'http://localhost/main/test'

        >>> system.uri = ''
        >>> route.pop()
        'main'
        >>> url_for('test')
        '/test'

    """
    return construct_url(system.uri, route, a, k)

def url_for_app(*a,**k):
    """Return a URL for the current app."""
    if a and a[0][0] <> '/':
        b = ('/'+a[0],) + a[1:]
    return construct_url(system.uri,[],b,k)

def url_for_page(*args, **keywords):
    """Returns a URL for a page within the current app"""
    return url_for('/' + system.app.name, *args,**keywords)

def abs_url_for(*a, **k):
    """
    calculates absolute url
    """
    if a[0] in ['http://','https://']:
        url = a[0]
        args = a[1:]
    else:
        if request.port == '443':
            protocol = 'https'
        else:
            protocol = 'http'
        host = request.server
        uri = '/'.join(request.uri.split('/')[:-1])
        port = (request.port not in ['80','443']) and (':%s'%request.port) or ''
        if len(a[0][0]) and a[0][0] == '/':
            url = '%s://%s%s' % (protocol,host,port)
        else:
            url = '%s://%s%s/%s' % (protocol,host,port,uri)
        args = a
    new_uri = '/'.join(str(i) for i in a)
    if new_uri.startswith('//'):
        result = url + new_uri[1:]
    else:
        result = url + new_uri
    if k:
        result = result + '?' + ('&'.join('%s=%s' % (j,v) for j,v in k.items()))
    return result

def lorem():
    """Returns some sample latin text to use for prototyping."""
    return """
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
        incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
        ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
        voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
        proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
        """

def plural(s,cnt):
    """ return string "s" as plural or not based on count (cnt)

        >>> plural(' record ', 2)
        ' records'
        >>> plural('entity', 1)
        'entity'
        >>> plural(' entity', 0)
        ' entities'
    """
    s = s.rstrip()
    if cnt==1:
        return s
    elif s[-1]<>'y':
        return "{}{}".format(s,'s')
    else:
        return "{}{}".format(s[:-1],'ies')


if __name__ == '__main__':
    import unittest

    class HelpersTest(unittest.TestCase):

        #--------- tests
        def test_construct_uri(self):
            # URLs within the same app
            self.assertEqual(construct_url('/dz/www',('info',),('index',),{}),'/dz/www/info/index')
            self.assertEqual(construct_url('/dz/www',('info','index'),('other',),{}),'/dz/www/info/other')
            self.assertEqual(construct_url('/dz/www',('info','index'),('other/page1',),{}),'/dz/www/info/other/page1')
            self.assertEqual(construct_url('/dz/www',('info','index'),('other/page1','new'),{}),'/dz/www/info/other/page1/new')
            self.assertEqual(construct_url('/dz/www',('cart',),('list',),{}),'/dz/www/cart/list')
            self.assertEqual(construct_url('/dz/www',('cart','list'),('add',),{}),'/dz/www/cart/add')
            self.assertEqual(construct_url('/dz/www',('cart','list','add'),('add','multiple',),{}),'/dz/www/cart/list/add/multiple')
            self.assertEqual(construct_url('/dz/www',('cart','list','add'),('sub',),{}),'/dz/www/cart/list/sub')
            self.assertEqual(construct_url('/dz/www',('cart','list','add','single','item'),('sub',),{}),'/dz/www/cart/list/add/single/sub')

            # URLs referring to separate apps
            self.assertEqual(construct_url('/dz/www',('info',),('/home',),{}),'/dz/www/home')
            self.assertEqual(construct_url('/dz/www',('info',),('/home/page1',),{}),'/dz/www/home/page1')
            self.assertEqual(construct_url('/dz/www',('info',),('/home','page1'),{}),'/dz/www/home/page1')
            self.assertEqual(construct_url('/dz/www',('info',),('/',),{}),'/dz/www')

            # absolute URLs
            self.assertEqual(construct_url('/dz/www',('info',),('http://localhost/login',),{}),'http://localhost/login')

        def no(self):
            self.assertEqual(url_for(action='action1'),'index.py?app=noapp&action=action1')
            self.assertEqual(url_for(con='con1'),'index.py?app=noapp&con=con1')
            self.assertEqual(url_for(con='con1',action='action1'),'index.py?app=noapp&con=con1&action=action1')
            self.assertEqual(url_for(app='app1',con='con1',action='action1'),'index.py?app=app1&con=con1&action=action1')
            self.assertEqual(url_for(app='app1',con='',action=''),'index.py?app=app1')

            self.assertEqual(url_for(app='app1',con=''),'index.py?app=app1')
            self.assertEqual(url_for(app='app1',con='con1'),'index.py?app=app1&con=con1')
            self.assertEqual(url_for(app='',con='con1'),'index.py?app=noapp&con=con1')
            self.assertEqual(url_for(app='app1',con=''),'index.py?app=app1')

        def test_text_input(self):
            system.in_form = True
            self.assertEqual(text_input('name',size=2),'<input name="name" value="{{NAME}}" maxlength="40" type="text" class="text" size="40" />')
            self.assertEqual(text_input('name',size=2,value='Joe'),'<input name="name" value="Joe" maxlength="40" type="text" class="text" size="40" />')

    unittest.main()


