
from zoom import *
import os

def app():

    def f(b):
        return '<code style="margin-left:20px">%s</code>' % repr(b).replace('<','&lt;').replace('>','&gt;')

    def fmt(item):
        if hasattr(item, 'keys'):
            return '<table>%s</table>' % ''.join('<tr><td style="width:120px">%s</td><td>%s</td></tr>' % (f(k),f(item[k])) for k in item.keys())
        return f(item)

    if web.input(image='no').image == 'yes':
        return PNGResponse(file(system.theme_path + '/default/images/no_photo.png','rb').read())

    info = []
    info.append(('data', request.data))
    info.append(('request', request))
    info.append(('user', user))
    info.append(('session', session))
    info.append(('system', system))
    info.append(('config', system.config.__dict__))
    info.append(('ctx', web.ctx))
    info.append(('globals', globals()))

    t = ''.join(['<H1 style="margin-bottom:0.2em">%s</H1>%s' % (a,fmt(b)) for a,b in info])
    return HTMLResponse('<H1>images</H1><img src="debug?image=yes"> <img src="/static/icons/mailbox.png">'+t)

