
from model import *

css = """
div.edit-menu li { display: inline; margin-left:10px; }
div.edit-menu { float:right; margin-right: 20px; }

#input[type="file"] { background: red; line-height:30px; }

textarea.editor {
    width: 100%;
    height: 350px;
    border-color: #DBDBDB;
    overflow: auto;
    margin-top: 5px;
    margin-bottom: 5px;
}
"""

subapp = 'f'
collection_name = 'Files'
item_name = 'File'


class FileController(Controller):

    def new_button(self):
        return redirect_to(url_for(self.collection.url,'new'))
        
    def delete(self,name,confirm=True):
        if confirm != True:
            delete_file(name)
            return redirect_to(url_for(app,subapp))
            
    def upload_button(self,upload_file,*a,**k):
        if not hasattr(upload_file,'value'):
            message('File missing')
        else:
            name = upload_file.filename
            data = upload_file.value
            try:
                save_file(name,data)
            except IOError as e:
                if 'Permission denied' in e:
                    error('Permission denied')
                else:
                    raise
        return redirect_to(url_for(app,subapp))
        

class FileView(View):
    
    def __init__(self):
        system.app.menu = main_menu

    def index(self):
        actions = 'Upload',
        item_list = [(link_to(t, '/content/f/'+t),) for t in sorted(list_files())]
        return page(browse(item_list, labels=['File Name']), title='Files', actions=actions, css=css)


    def upload(self):
        action_url  = url_for(app,subapp)
        cancel_link = link_to('cancel',app,subapp)
        elements = [
            multipart_form(action=action_url),
            '<H1>Upload %s</H1><br><input name=upload_file type=file> ' % item_name,
            button('Upload Now',name='upload_button'),cancel_link,'<br>',
            '</form>',
        ]
        content = '\n'.join(elements)            
        page = Page(content)
        page.css = css
        return page

    def show(self,name):
        delete_link = link_to('delete',app,subapp,name,'delete')
        return Page('<H1>%s</H1>%s&nbsp;&nbsp;&nbsp;%s<br><br>url: <a href="%s">%s</a>' % (item_name,name,delete_link,file_url(name),file_url(name)))

    def delete(self,name,confirm=True):
        cancel_link = link_to('cancel',app,subapp)
        if confirm == True:
            return Page("""
                <H1>Delete %s</H1>
                Are you sure you want to delete the file named <strong>%s</strong> ?<br><br>
                <dz:form confirm=False><dz:button label="Yes, I'm sure. Please delete." name=delete_button>&nbsp;&nbsp;%s</form>""" % (item_name,name,cancel_link))


controller = FileController()
view = FileView()


