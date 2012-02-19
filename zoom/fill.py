"""Implements filling of templates"""

__all__ = ['fill','viewfill']

import re
from utils import unisafe

tag_parts = re.compile(r"""(\w+)\s*=\s*"([^"]*)"|(\w+)\s*=\s*'([^']*)'|(\w+)\s*=\s*([^\s]+)\s*|"([^"]*)"|(\w+)""")

def _fill(tag_start,tag_end,text,callback):

    def replace_tag(match):

        name     = match.groups(1)[0].lower()
        rest     = match.group(0)[len(name)+len(tag_start):-len(tag_end)]
        parts    = tag_parts.findall(rest)
        keywords = dict(a and (a,b) or c and (c,d) or e and (e,f) for (a,b,c,d,e,f,g,h) in parts if a or c or e)
        args     = [g or h for (a,b,c,d,e,f,g,h) in parts if g or h]

        result = unicode(callback(name,*args,**keywords))
        if result == None: 
            result = match.group(0)
        return result
    
    expr = """%(tag_start)s([a-z0-9_]+)\s*(.*?)%(tag_end)s""" % dict(tag_start=tag_start,tag_end=tag_end)
    innerre = re.compile(expr, re.IGNORECASE)
    result = []
    lastindex = 0
    
    for outermatch in re.finditer("<!--.*?-->",text):
        text_between = text[lastindex:outermatch.start()]
        new_text = innerre.sub(replace_tag, text_between)
        result.append(new_text)
        lastindex = outermatch.end()
        result.append(outermatch.group())
    text_after = text[lastindex:]
    result.append(innerre.sub(replace_tag,unisafe(text_after)))
    
    return ''.join(result)

def fill(text, callback):
    """
    Replaces the <z:_ > tags in a template

    >>> fill('test <z:this>', lambda a: 'one')
    u'test one'

    """
    return _fill('<z:','>',text,callback)

def viewfill(text, callback):
    return _fill('{{','}}', text,callback)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
