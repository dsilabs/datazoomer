
import os
import datetime
import pickle

from zoom import *
from zoom.storage import Model

class ContentPage(Model): pass


css = """
div.edit-menu li { display: inline; margin-left:10px; }
div.edit-menu { float:right; margin-right: 20px; }
div.content {
    font-size: 14px;
    }

div.page-info {
    width: 90%;
}

div.page-info input.text_field {
    width: 55%;
}

div.page-info textarea {
    width: 95%;
}

div.page-info textarea {
    width: 700px;
    height: 80px;
}

input, textarea {
    margin: 0;
}

textarea#page-content {
    height: 400px;
}

span.page-title {
    float:right;
    font-size:20px;
    line-height:35px;
    width=50%;
}

textarea.page-content {
    width: 75%;
    display:block;
    height: 350px;
    border-color: #DBDBDB;
    overflow: auto;
    margin-top: 5px;
    margin-bottom: 5px;
}

input.page-field {
    width: 75%;
    sborder-color: #DBDBDB;
    soverflow: auto;
    margin-top: 5px;
    margin-bottom: 5px;
}

textarea.page-meta {
    width: 75%;
    height: 50px;
    border-color: #DBDBDB;
    overflow: auto;
    margin-top: 5px;
    margin-bottom: 5px;
}

textarea.editor {
    width: 100%;
    height: 350px;
    border-color: #DBDBDB;
    overflow: auto;
    margin-top: 5px;
    margin-bottom: 5px;
}
"""



main_menu = [
    ('p','Pages','p'),
    ('s','Snippets','s'),
    ('i','Images','i'),
    ('f','Files','f'),
    ]

if user.is_admin:
    main_menu.append(
    ('sitemap','Sitemap','sitemap'),
    )

app = system.app.url

images_dir = os.path.join(system.config.sites_path,system.server_name,'content','images')
files_dir = os.path.join(system.config.sites_path,system.server_name,'content','files')

#===========================================================
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

def list_pages():
    return [a.page_name+'.html' for a in ContentPage.all()] or ['index.html']
    
def load_page(page_name,create=0):
    if page_name == '-':
        return ('','','','')
    q = ContentPage.find(page_name=page_name)
    if q:
        item = q[0]
        return item.title,item.content,item.description,item.keywords
    else:
        if create:
            doc = open('new.txt').read()
        else:            
            doc = "<H1>Missing Page</H1>That page appears to be missing.<br>"
        return '<dz:site_name>',doc,'',''                                
    return

def save_page(page_name,content,title,new_page_name,description,keywords):
    delete_page(page_name)
    new_name = make_page_name(new_page_name)
    delete_page(new_name)
    item = ContentPage(page_name=new_name,title=title,content=content,description=description,keywords=keywords)
    item.put()
    return new_name    

def delete_page(page_name):
    q = ContentPage.find(page_name=page_name)
    for item in q:
        item.delete()
    
#===========================================================
def list_images():
    items = os.listdir(images_dir)
    items.sort()
    return items

def image_url(name):
    return '/images/%s' % name

def delete_image(name):
    os.remove(os.path.join(images_dir,name))

def save_image(name,data):
    pathname = os.path.join(images_dir,name)
    f=file(pathname,'wb')
    f.write(data)
    f.close()

#===========================================================
def list_files():
    items = os.listdir(files_dir)
    items.sort()
    return items

def file_url(name):
    return '/files/%s' % name

def delete_file(name):
    os.remove(os.path.join(files_dir,name))

def save_file(name,data):
    pathname = os.path.join(files_dir,name)
    f=file(pathname,'wb')
    f.write(data)
    f.close()

    
if __name__ == '__main__':
    for item in list_images():
        print item 
        

