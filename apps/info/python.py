
from zoom import *
import sys
import markdown
import platform

def view():

    items = {}
    items['version'] = sys.version

    try:
        items['markdown version'] = markdown.__version__.version
    except:
        try:
            items['markdown version'] = markdown.version
        except:
            items['markdown version'] = 'unable to get version info'

    items['path'] = '<br>'.join(sys.path)
    items['platform'] = sys.platform
    items['node'] = platform.node()
    
    fmt = '<tr><td><pre>%-20s</pre></td><td><pre>%s</pre></td></tr>\n'
    x = [(fmt % (k,v)) for k,v in items.items()]
    t = '<table>%s</table>' % (''.join(x))
    return page(t, title='Python')
    
    
