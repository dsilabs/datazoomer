
import zoom
from zoom import *
import os

def app():
    if web.input(image='no').image == 'yes':
        return PNGResponse(file('../themes/default/images/no_photo.png','rb').read())
    info = []
    info.append(('System',zoom.system.__dict__))
    info.append(('Config',config.__dict__))
    info.append(('Zoom',zoom.__dict__))
    info.append(('Environment',os.environ))
    info.append(('Context',web.ctx))
    t = ''.join(['<H1>%s</H1>%s' % (a,repr(b)) for a,b in info])
    return HTMLResponse('Hello, world.\n<br><img src="?image=yes">'+t)


