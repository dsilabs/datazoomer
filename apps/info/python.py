
from zoom import *
import sys

def view():

    items = {}
    items['version'] = sys.version
    items['path'] = '<br>'.join(sys.path)
    items['platform'] = sys.platform
    
    fmt = '<tr><td><pre>%-20s</pre></td><td><pre>%s</pre></td></tr>\n'
    x = [(fmt % (k,v)) for k,v in items.items()]
    t = '<table>%s</table>' % (''.join(x))
    return page(t, title='Python')
    
    
