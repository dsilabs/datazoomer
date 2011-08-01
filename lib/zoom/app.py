
from zoom import *

def app():
    if web.input(image='no').image == 'yes':
        return PNGResponse(file('../themes/default/images/no_photo.png','rb').read())
    return HTMLResponse('Hello, world.\n<br><img src="?image=yes">')


