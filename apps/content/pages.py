
from model import *

css = """
div.edit-menu li { display: inline; margin-left:10px; }
div.edit-menu { float:right; margin-right: 20px; }

textarea.editor {
    width: 100%;
    height: 350px;
    border-color: #DBDBDB;
    overflow: auto;
    margin-top: 5px;
    margin-bottom: 5px;
}
"""


class CollectionController(Controller):

    def add_button(self,*args,**values):
        self.collection.fields.update(**values)
        item = self.collection.model.__class__(**self.collection.fields.evaluate())
        id = item.put()
        return redirect_to(url_for(self.collection.url))
    
    def update_button(self,id,*args,**values):
        self.collection.fields.update(**values)
        item = self.collection.model.get(id)
        if item:
            item.update(**self.collection.fields.evaluate())
            item.put()
        return redirect_to(url_for(self.collection.url,id))

    def new_button(self):
        return redirect_to(url_for(self.collection.url,'new'))
        
    def delete(self,id,confirm=True):
        if not confirm:
            item = self.collection.model.get(id)
            if item:
                name = item.name
                item.delete()
                message('deleted %s'%name)
            return redirect_to(url_for(self.collection.url))

def columns(obj,names):
    result = []
    for name in names:
        if hasattr(obj,name):
            result.append(getattr(obj,name))
        else:
            result.append('&nbsp;')
    return result            

class ContentView(View):

    def show(self,page='index'):
        if user.is_admin:
            menu = div(ul([link_to('edit page',page,'edit'),link_to('list all','list-all')]),Class='edit-menu')
        else:
            menu = ''        
        raw_content = load_page(page)
        content = markdown(raw_content)
        page = Page(menu+content)
        page.css = css
        return page
                
    def edit(self,page='index'):
        raw_content = load_page(page)
        elements = [
            form(action='/'.join([route[0],route[1]])),
            '<b>%s</b>'%page,
            save_button(),link_to('cancel','/'+route[0],'pages',page),'<br>',
            '<textarea name=text class=editor>%s</textarea><br>'%raw_content,
            save_button(),link_to('cancel','/'+route[0],'pages',page),'<br>',
            '</form>'
        ]
        content = '\n'.join(elements)            
        page = Page(content)
        page.css = css
        return page

    def new(self):
        values = dict(fields=self.collection.fields.edit(),item_name=self.collection.item_name)
        page = Page('new',values.get)
        page.js = self.js
        return page
        
    def delete(self,id,confirm=True):
        if confirm:
            system.app.menu = (('index',self.collection.name,'index'),)
            item = self.collection.model.get(id)
            name = item.name
            return Page("""
                <H1>Delete %s</H1>
                Are you sure you want to delete <strong>%s</strong> ?<br><br>
                <dz:form confirm=False><dz:button label="Yes, I'm sure. Please delete." name=delete_button>&nbsp;&nbsp;<dz:cancel></form>""" % (self.collection.item_name,name))


view = ContentView()


