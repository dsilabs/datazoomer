
from model import *

scss = """
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


class ImageController(Controller):

    def new_button(self):
        return redirect_to(url_for(self.collection.url,'new'))
        
    def delete(self,name,confirm=True):
        if confirm != True:
            delete_image(name)
            return redirect_to(url_for(app,'i'))
            
    def upload_button(self,upload_file,*a,**k):
        if not hasattr(upload_file,'value'):
            message('File missing')
        else:
            name = upload_file.filename
            data = upload_file.value
            try:
                save_image(name,data)
            except IOError as e:
                if 'Permission denied' in e:
                    error('Permission denied')
                else:
                    raise
        return redirect_to(url_for(app,'i'))
        

class ImageView(View):
    collection_name = 'Images'
    item_name = 'Image'
    
    def __init__(self):
        system.app.menu = main_menu

    def index(self):
        actions = 'Upload',
        item_list = [(link_to(t, '/content/i/'+t),) for t in sorted(list_images())]
        return page(browse(item_list, labels=['Image Name']), title='Images', actions=actions, css=css)

    def upload(self):
        action_url  = url_for(app,'i')
        cancel_link = link_to('cancel',app,'i')
        elements = [
            multipart_form(action=action_url),
            '<H1>Upload %s</H1><br><input name=upload_file type=file> ' % self.item_name,
            button('Upload Now',name='upload_button'),cancel_link,'<br>',
            '</form>',
        ]
        content = '\n'.join(elements)            
        page = Page(content)
        page.css = css
        return page

    def show(self,name):
        menu = link_to('delete image',app,'i',name,'delete')
        page = Page('<H1>%s</H1><b>%s</b>&nbsp;&nbsp;&nbsp;%s<br><br><img src="%s" border=0>' % (self.item_name,name,menu,image_url(name)))
        page.css = css
        return page
        
    def delete(self,name,confirm=True):
        cancel_link = link_to('cancel',app,'i')
        if confirm:
            return Page("""
                <H1>Delete %s</H1>
                Are you sure you want to delete the image named <strong>%s</strong> ?<br><br>
                <dz:form confirm=False><dz:button label="Yes, I'm sure. Please delete." name=delete_button>&nbsp;&nbsp;%s</form>""" % (self.item_name,name,cancel_link))


controller = ImageController()
view = ImageView()


