"""
    zoom.component

    Components encapsulate all of the parts that are required to make a
    component appear on a page.  This can include HTML, CSS and Javascript
    parts and associated libraries.

    Components parts are assembled in the way that kind of part
    needs to be treated.  For example HTML parts are simply joined
    together in order and returned.  CSS parts on the other hand are
    joined together but any duplicate parts are ignored.

    When a caller supplies JS or CSS as part of the component being assembled
    these extra parts are submitted to the system to be included in thier
    proper place within a response (typically a page template).

    The Component object is currently experimental and is intended to be used
    in future releases.
"""

from zoom.state import system
from zoom.utils import OrderedSet

class Component(object):
    """component of a page response

    >>> c = Component()
    >>> c
    <Component: {'html': []}>

    >>> c += 'test'
    >>> c
    <Component: {'html': ['test']}>

    >>> c += dict(css='mycss')
    >>> c
    <Component: {'html': ['test'], 'css': OrderedSet(['mycss'])}>

    >>> c += dict(css='mycss')
    >>> c
    <Component: {'html': ['test'], 'css': OrderedSet(['mycss'])}>

    >>> c += 'test2'
    >>> c.parts
    {'html': ['test', 'test2'], 'css': OrderedSet(['mycss'])}

    >>> Component() + 'test1' + 'test2'
    <Component: {'html': ['test1', 'test2']}>

    >>> Component() + 'test1' + dict(css='mycss')
    <Component: {'html': ['test1'], 'css': OrderedSet(['mycss'])}>

    >>> page2 = \\
    ...    Component() + \\
    ...    '<h1>Title</h1>' + \\
    ...    dict(css='mycss') + \\
    ...    dict(js='myjs') + \\
    ...    'page body goes here'
    >>> t = (
    ...    "<Component: {'html': ['<h1>Title</h1>', 'page body goes here'], "
    ...    "'css': OrderedSet(['mycss']), 'js': OrderedSet(['myjs'])}>"
    ... )
    >>> #print repr(page2) + '\\n' + t
    >>> repr(page2) == t
    True
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):
        """construct a Component

        >>> Component()
        <Component: {'html': []}>

        >>> Component('body')
        <Component: {'html': ['body']}>

        >>> Component('body', css='css1')
        <Component: {'html': ['body'], 'css': OrderedSet(['css1'])}>

        >>> t = Component('body', css='css1', js='js1')
        >>> repr(t) == (
        ...     "<Component: {"
        ...     "'html': ['body'], "
        ...     "'css': OrderedSet(['css1']), "
        ...     "'js': OrderedSet(['js1'])"
        ...     "}>"
        ... )
        True
        """
        self.parts = {
            'html': list(args),
        }
        self += kwargs

    def __iadd__(self, other):
        """add something to a component

        >>> page = Component('<h1>Title</h1>')
        >>> page += dict(css='mycss')
        >>> page += 'page body goes here'
        >>> page += dict(js='myjs')
        >>> result = (
        ...     "<Component: {"
        ...     "'html': ['<h1>Title</h1>', 'page body goes here'], "
        ...     "'css': OrderedSet(['mycss']), "
        ...     "'js': OrderedSet(['myjs'])"
        ...     "}>"
        ... )
        >>> result == repr(page)
        True

        >>> page = Component('test')
        >>> page += dict(html='text')
        >>> page
        <Component: {'html': ['test', 'text']}>

        """
        kind = type(other)
        if kind == str:
            self.parts['html'].append(other)
        elif kind == dict:
            for key, value in other.items():
                part = self.parts.setdefault(key, OrderedSet())
                if key == 'html':
                    if type(value) == list:
                        part.extend(value)
                    else:
                        part.append(value)
                else:
                    if type(value) == list:
                        part |= value
                    else:
                        part |= [value]
        elif kind == Component:
            for key, value in other.parts.items():
                part = self.parts.setdefault(key, OrderedSet())
                if key == 'html':
                    part.extend(value)
                else:
                    part |= value
        return self

    def __add__(self, other):
        """add a component to something else

        >>> (Component() + 'test1' + dict(css='mycss')) + 'test2'
        <Component: {'html': ['test1', 'test2'], 'css': OrderedSet(['mycss'])}>

        >>> Component() + 'test1' + dict(css='mycss') + dict(css='css2')
        <Component: {'html': ['test1'], 'css': OrderedSet(['mycss', 'css2'])}>
        """
        result = Component()
        result += self
        result += other
        return result

    def __repr__(self):
        return '<Component: {!r}>'.format(self.parts)


def component(*args, **kwargs):
    """assemble parts of a component

    >>> system.setup()
    >>> system.css
    OrderedSet()

    >>> component('test', css='mycss')
    'test'
    >>> system.css
    OrderedSet(['mycss'])

    >>> component('test', 'two', css=['mycss','css2'], js='myjs')
    'testtwo'
    >>> system.css
    OrderedSet(['mycss', 'css2'])
    >>> system.js
    OrderedSet(['myjs'])

    >>> component('test', js='js2')
    'test'
    >>> system.js
    OrderedSet(['myjs', 'js2'])

    >>> system.setup()
    >>> component('test', js=[])
    'test'
    >>> system.js
    OrderedSet()
    """
    is_iterable = lambda a: hasattr(a, '__iter__')
    as_iterable = lambda a: not is_iterable(a) and (a,) or a
    parts = {
        'html': args,
    }
    for key, value in kwargs.items():
        part = parts.setdefault(key, OrderedSet())
        if key == 'html':
            part.extend(as_iterable(value))
        else:
            part |= OrderedSet(as_iterable(value))
    for key in ['css', 'js', 'styles', 'libs']:
        part = getattr(system, key)
        part |= parts.get(key, [])
    return ''.join(parts['html'])

