# Copyright (c) 2005-2011 Dynamic Solutions Inc. (support@dynamic-solutions.com)
#
# This file is part of DataZoomer.
#
# DataZoomer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DataZoomer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


def li(items):
    """
    generate list items

        >>> li(['this','that'])
        '<li>this</li><li>that</li>'

    """
    return ''.join('<li>%s</li>' % item for item in items)

def ul(items, Class=''):
    """
    generate an unordered list
        
        >>> ul(['this','that'])
        '<ul><li>this</li><li>that</li></ul>'

    """
    class_attr = Class and ' class="%s"' % Class or ''
    return '<ul%s>%s</ul>' % (class_attr, ''.join('<li>%s</li>' % item for item in items))

def tag(tag_text,content='',*args,**keywords):
    """
    generates an HTML tag

        >>> tag('div', 'some content')
        '<div>some content</div>'

        >>> tag('a', href='http://www.google.com')
        '<a href="http://www.google.com" />'
    
    """
    tag_type = tag_text.lower()
    singles = ''.join([' %s' % arg.lower() for arg in args])
    attribute_text = ''.join([' %s="%s"' % (key.lower(),keywords[key]) for key in keywords])
    if content or tag_type in ['textarea']:
        return '<%s%s%s>%s</%s>' % (tag_type,singles,attribute_text,content,tag_type)
    else:
        return '<%s%s%s />' % (tag_type,singles,attribute_text)
     
def div(content,**keywords):
    """
    generates an div tag

        >>> div('some content')
        '<div>some content</div>'

    """
    return tag('div',content,**keywords)
     
