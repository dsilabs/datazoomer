
from model import *
from zoom.fill import fill

def columns(obj,names):
    result = []
    for name in names:
        if hasattr(obj,name):
            result.append(getattr(obj,name))
        else:
            result.append('&nbsp;')
    return result            

class ContentView:

    def __call__(self,*a,**k):

        # The user has specificially selected the index page, but the default zoom.App behaviour
        # wipes out the 'index' parameter because it assumes that we want to run the index method.
        # In this case, we actually want to show the index content page.
        if route == ['content','index']:
            return self.show()

        if a:
            if a[-1] == 'sedit':
                result = self.edit('/'.join(a[0:-1]),**k)

            elif a[-1] == 'delete':
                result = self.delete('/'.join(a[0:-1]))

            elif a[-1] == 'sitemap':
                result = self.sitemap()

            else:
                result = self.show('/'.join(a))
        else:
            if user.is_manager:
                return redirect_to('/content/p')
            result = self.show()
        return result                            

    def index(self):
        return self.show()
        
    def sitemap(self):
        def exclude(page):
            keywords = ['test', 'draft', 'test-page']
            for keyword in keywords:
                if page.startswith(keyword) or page.endswith(keyword+'.html'):
                    return True
            return False

        tpl = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
%s</urlset>"""

        url_tpl = """    <url>
         <loc>%(loc)s</loc>
         <changefreq>%(changefreq)s</changefreq>
    </url>
"""
        pages = [
                dict(
                    loc = abs_url_for('/', page),
                    changefreq = 'daily',
                    priority = '0.5',
                    ) for page in sorted(list_pages()) if not exclude(page)]

        content = tpl % (''.join(url_tpl % page for page in pages))

        from zoom.response import TextResponse
        return TextResponse(content)

    def show(self, page_name='index'):

        page_name = page_name or 'index'
        menu_name = page_name.split('/')[0]
        system.app.menu = get_menu(menu_name)

        if user.is_manager:
            menu_items = []
            menu_items.append(link_to('edit', app, 'p', page_name, 'edit'))
            if page_name != 'index':
                menu_items.append(link_to('delete', app, 'p', page_name, 'delete'))
            menu_items.append(link_to('list', app, 'p'))
            menu = div(ul(menu_items), Class='edit-menu')
        else:
            menu = ''        
        
        title, content, description, keywords = load_page(page_name, user.is_manager)

        p = page(menu + markdown(content), css=css, template='content')
        p.title = title
        p.description = description
        p.keywords = keywords
        
        return p
                
view = ContentView()


