
from zoom import *
from zoom.manager import DEFAULT_SYSTEM_APPS

def app():
    def list_apps(app_names):
        t = []
        tpl = '<div class="app-icon"><a href="/%(name)s"><img src="/static/dz/icons/%(icon)s.png" border=0></a><a href="/%(name)s">%(title)s</a></div>'
        apps = [manager.get_app(name) for name in app_names]
        apps.sort(key=lambda a: a.title)
        for app in apps:
            if app.visible:
                icon = app.icon
                name = app.name
                title = app.title
                t.append(tpl % dict(icon=icon,name=name,title=title))
        return '<div class="app-icons">%s</div><div style="clear:both;"></div>' % ''.join(t)
            
    css = """
        .app-icons { float:left; width:100%; }
        .app-icon  { float:left; width:100px; height: 100px; display: inline; margin:10px; margin-top: 0; text-align:center; }
        .app-icon img { display: block; margin: 0px auto; height: 60px; }
        @media (max-width: 580px) {
            .app-icon  { float:left; width:70px; display: inline; margin:10px; text-align:center; }
            .app-icon img { display: block; margin: 0px auto; height: 50px; }
        }
    """

    standard_apps = manager.get_standard_app_names()
    if 'home' in standard_apps:
        standard_apps.remove('home')
    system_apps = get_setting('system') or DEFAULT_SYSTEM_APPS

    panels = [list_apps(standard_apps)]
    
    if user.is_admin:
        other_apps = [item for item in manager.apps if item not in standard_apps+system_apps+['home']]
        panels.append('<H1>Unregistered</H1>%s' % list_apps(other_apps))
    
    content = ''.join(panels)    
    return page(content, css=css, title='Home')

