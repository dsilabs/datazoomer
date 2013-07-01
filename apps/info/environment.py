
from zoom import *

def view():
    
    fmt = '%-20s: %s<br>\n'
    x = [(fmt % (k,v)) for k,v in os.environ.items()]
    t = ''.join(x)
    return page(t, title='Environment')
    
    
