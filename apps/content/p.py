
from model import *

markitup_head = """
<script type="text/javascript" src="/static/markitup/jquery.markitup.js"></script>
<script type="text/javascript" src="/static/markitup/sets/zoom/set.js"></script>
<link rel="stylesheet" type="text/css" href="/static/markitup/skins/simple/style.css" />
<link rel="stylesheet" type="text/css" href="/static/markitup/sets/zoom/style.css" />
<script type="text/javascript" >
   $(document).ready(function() {
       $("#page-content").markItUp(mySettings);
   });
</script>
<style>
    .content .field_label {
        width: 15%;
        min-width: 15%;
    }
    .markitup {
        width: 100%;
    }
    div.markItUpHeader ul {
        margin-left: 0.5em;
    }
    textarea#CONTENT {
        height: 400px;
        }
</style>
"""

class PageController(Controller):

    def save_button(self,page_name,*a,**k):
        new_page_name = k.get('new_page_name',None)
        if not new_page_name:
            error('please enter a name for this page (example: about-us.html)')
        else:            
            new_name = make_page_name(new_page_name)
            if len(new_name) < 2:
                error('page name needs be at least 2 characters long')
            else:
                old_pages = list_pages()
                new_page_name = save_page(new_name,**k)
                url = url_for('/'+new_page_name+'.html')
                page_link = '<a href="%s">%s</a>' % (url,new_page_name+'.html')
                if not new_page_name+'.html' in old_pages:
                    logger.activity(system.app.name, '%s created page %s' % (user.link, page_link))
                else:
                    logger.activity(system.app.name, '%s edited page %s' % (user.link, page_link))
                return redirect_to(url)

    def delete_button(self,*a,**k):
        confirm = k.get('confirm',True)
        if confirm=='False':
            page_name = '/'.join(a[:-1])
            message('<b>%s</b> deleted' % page_name)
            delete_page(page_name)
            logger.activity(system.app.name, '%s deleted page %s.html' % (user.link, page_name))
            return redirect_to(url_for(app,'p'))


class PageView:

    def __call__(self,*a,**k):
        if a:
            if a[-1] == 'edit':
                result = self.edit('/'.join(a[0:-1]),**k)
            elif a[-1] == 'delete':
                result = self.delete('/'.join(a[0:-1]))
            elif a[-1] == 'new-page':
                result = self.edit('-')
            else:
                result = self.show('/'.join(a))
        else:
            result = self.index()
        return result                            

    def index(self,page_name='index'):
        system.app.menu = main_menu 
        actions = 'New Page',
        page_list = [(link_to(t, '/'+t),) for t in sorted(list_pages())]
        return page(browse(page_list, labels=['Page Name']), title='Pages', actions=actions)

    def edit(self,page_name,title=None,content=None,new_page_name=None,description=None,keywords=None,**k):

        (saved_title,saved_content,saved_description,saved_keywords) = load_page(page_name,user.is_manager)
        title = title or saved_title
        content = content or saved_content
        description = description or saved_description
        keywords = keywords or saved_keywords
        
        content_placeholder = '<<content>>'
        title_placeholder = '<<title>>'
        description_placeholder = '<<description>>'
        keywords_placeholder = '<<keywords>>'

        action_url  = url_for(app,'p',page_name,'edit')
        if page_name != '-':
            cancel_link = link_to('cancel',app,page_name)
        else:
            cancel_link = link_to('cancel',app)
        new_name = make_page_name(new_page_name or page_name!='-' and page_name or '')
        page_title = (page_name!='-' and page_name or 'new page')

        elements = [
            form(action=action_url),
            '<div class="page-info">',
                save_button(), cancel_link,
                '<span class="page-title"><b>%s</b></span>' % page_title,
            '<div class=field>',
                '<label>Page Title</label><br>',
                '<input name=title class="text_field" value="%s">' % title_placeholder,
            '</div>',
            '<div class=field>',
                '<label>Page Description</label><br>',
                '<textarea name=description cols=80 class="memo_field">%s</textarea>' % description_placeholder,
            '</div>',
            '<div class=field>',
                '<label>Page Content</label><br>',
                '<textarea name=content id="page-content" class="memo_field">%s</textarea>' % content_placeholder,
            '</div>',
            '<div class=field>',
                '<label>Page Name</label><br>',
                '<input name=new_page_name size=80 class=text_field value="%s">' % (new_name and new_name+'.html' or ''),
            '</div>',
            '<div class=field>',
            '<label>Page Keywords</label><br>',
                '<textarea name=keywords cols=80 class=memo_field>%s</textarea>'%keywords_placeholder,
            '</div>',
            '<br>',
            save_button(), cancel_link,
            '</form>',
            '</div>',
        ]

        page = Page()
        page.content = '\n'.join(elements)            
        page.css = css
        page.head = markitup_head
        result = page.render()
        result.content = result.content.replace(content_placeholder, unisafe(htmlquote(content)))
        result.content = result.content.replace(title_placeholder, title)
        result.content = result.content.replace(description_placeholder, description)
        result.content = result.content.replace(keywords_placeholder, keywords)
        return result

    def delete(self,page_name,confirm=True):
        page_name = page_name or 'index'
        cancel_link = link_to('cancel','/'+page_name+'.html')
        if confirm:
            return Page("""
                <H1>Delete %s</H1>
                Are you sure you want to delete the page named <strong>%s</strong> ?<br><br>
                <dz:form confirm=False><dz:button label="Yes, I'm sure. Please delete." name=delete_button>&nbsp;&nbsp;%s</form>""" % (page_name,page_name,cancel_link))


controller = PageController()
view = PageView()


