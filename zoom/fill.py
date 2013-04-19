"""
    fills templates
"""

from tools import unisafe
import re

parts_re = r"""(\w+)\s*=\s*"([^"]*)"|(\w+)\s*=\s*'([^']*)'|(\w+)\s*=\s*([^\s]+)\s*|("")|"([^"]*)"|(\w+)"""
tag_parts = re.compile(parts_re)

def fill(tag_start, tag_end, text, callback):

    def replace_tag(match):

        name     = match.groups(1)[0].lower()
        rest     = match.group(0)[len(name)+len(tag_start):-len(tag_end)]
        parts    = tag_parts.findall(rest)
        keywords = dict(a and (a,b) or c and (c,d) or e and (e,f) for (a,b,c,d,e,f,g,h,i) in parts if a or c or e)
        args     = [h or i or "" for (a,b,c,d,e,f,g,h,i) in parts if h or i or g]

        result = callback(name, *args, **keywords)
        if result == None: 
            result = match.group(0)
        return unisafe(result)
    
    expr = """%(tag_start)s([a-z0-9_]+)\s*(.*?)%(tag_end)s""" % dict(tag_start=tag_start, tag_end=tag_end)
    innerre = re.compile(expr,re.IGNORECASE)
    
    result = []
    lastindex = 0
    
    for outermatch in re.finditer("<!--.*?-->",text):
        text_between = text[lastindex:outermatch.start()]
        new_text = innerre.sub(replace_tag, unisafe(text_between))
        result.append(new_text)
        lastindex = outermatch.end()
        result.append(outermatch.group())
    text_after = text[lastindex:]
    result.append(innerre.sub(replace_tag, unisafe(text_after)))
    
    return u''.join(unisafe(x) for x in result)

def dzfill(text,callback):
    return fill('<dz:', '>', text, callback)

def viewfill(text,callback):
    return fill('{{', '}}', text, callback)

