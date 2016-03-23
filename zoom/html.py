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

def tag(element, content=None, *args, **kwargs):
    """
    generates an HTML tag

        >>> tag('div', 'some content')
        '<div>some content</div>'

        >>> tag('a', href='http://www.google.com')
        '<a href="http://www.google.com" />'
    
    """
    empty = ['area', 'base', 'br', 'col', 'command', 'embed', 'hr', 'img',
             'input', 'link', 'meta', 'param', 'source']

    name = element.lower()
    parts = \
            [name] + \
            [str(a).lower for a in args] + \
            ['{}="{}"'.format(k.lower(), v) for k, v in kwargs.items()]

    if content == None or name in empty:
        return '<{} />'.format(' '.join(parts))
    else:
        return '<{}>{}</{}>'.format(' '.join(parts), content, name)

     
def div(content='', **kwargs):
    """
    generates an div tag

        >>> div('some content')
        '<div>some content</div>'

        >>> div('')
        '<div></div>'

        >>> div(Class='header')
        '<div class="header"></div>'


    """
    return tag('div', content, **kwargs)
     
def h1(text):
    return '<h1>{}</h1>'.format(text)

def h2(text):
    return '<h2>{}</h2>'.format(text)

def h3(text):
    return '<h3>{}</h3>'.format(text)


# Bootstrap Wrappers
#----------------------------------------------------------------------------

def glyphicon(icon, **kwargs):
    """generates a glpyhicon span

    >>> glyphicon('heart')
    '<span class="glyphicon glyphicon-heart" aria-hidden="true"></span>'

    >>> glyphicon('heart', Class="special")
    '<span class="glyphicon glyphicon-heart special" aria-hidden="true"></span>'

    >>> glyphicon('heart', Class="special", style="color:red")
    '<span style="color:red" class="glyphicon glyphicon-heart special" aria-hidden="true"></span>'
    """
    additional_css_classes = kwargs.pop('Class', kwargs.pop('_class', ''))
    css_class = ' '.join(i for i in ['glyphicon glyphicon-{}'.format(icon),
                                     additional_css_classes] if i)
    attributes = {
        'aria-hidden': 'true',
        'class': css_class,
    }
    attributes.update(kwargs)
    return tag('span', '', **attributes)

