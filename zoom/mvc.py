"""
    zoom.mvc

    classes to support the model, view, controller pattern
"""


from inspect import getargspec

from request import data
from user import user
from exceptions import PageMissingException, UnauthorizedException


__all__ = ['View', 'Controller', 'authorize']


def as_attr(text):
    return text.replace('-', '_').lower()


def evaluate(o, i, *a, **k):
    name = as_attr(i)
    if hasattr(o, name):
        attr = getattr(o, name)
        method = callable(attr) and attr
        if method:
            try:
                return method(*a, **k)
            except TypeError, e:
                try:
                    sig = getargspec(method)
                except TypeError:
                    sig = None

                if sig and list(sig) == [['self'], None, None, None]:
                    # looks like an old style (parameterless) method
                    # so try calling it without parameters
                    return method()

                elif user.is_developer:
                    # its not a old style method issue, its just been
                    # called incorrectly so show the developer what
                    # got passed and raise the error as it was originall
                    # raised
                    print 'called', method, 'with', a, k
                raise e
        else:
            return attr


def remove_buttons(data):
    buttons = {}
    names = data.keys()
    for name in names:
        lname = name.lower()
        if lname.endswith('_button'):
            buttons[lname] = data[name]
            del data[name]
    return buttons, data


def authorize(*roles):
    def wrapper(func):
        def authorize_and_call(*args, **kwargs):
            if user.is_admin:
                return func(*args, **kwargs)
            for role in roles:
                if role in user.groups:
                    return func(*args, **kwargs)
            raise UnauthorizedException('Unauthorized')
        return authorize_and_call
    return wrapper


def can(action):
    """activity based authentication

    Tests to see if user can perform some activity.

        >>> class TheUser(object):
        ...
        ...     def __init__(self, name):
        ...         self.name = name
        ...
        ...     def can(self, action, thing):
        ...         return thing and thing.allows(self, action)

        >>> class Thing(object):
        ...
        ...     def __init__(self, name):
        ...         self.name = name
        ...
        ...     def allows(self, user, action):
        ...         return bool(user.name == 'joe' and action == 'edit') or \\
        ...                bool(user.name == 'sam' and action == 'delete')
        ...
        ...     def delete(self):
        ...         return 'deleted!'
        ...
        ...     @can('edit')
        ...     def update(self, name):
        ...         self.name = name
        ...         return 'hello {}!'.format(name)
        ...
        ...     @can('delete')
        ...     def zap(self):
        ...         return 'zapped!'
        ...

        >>> user.name = 'joe'
        >>> user.name
        'joe'

        >>> user.can('edit', None)
        False

        >>> thing = Thing(name='rain')

        >>> user.can('edit', thing)
        True

        >>> user.can('delete', thing)
        False

        >>> try:
        ...    thing.zap()
        ... except UnauthorizedException, e:
        ...    'access denied'
        'access denied'

        >>> user.name = 'sam'
        >>> try:
        ...    thing.update('clouds')
        ... except UnauthorizedException, e:
        ...    'sunshine prevails'
        'sunshine prevails'

        >>> thing.zap()
        'zapped!'

        >>> user = TheUser(name='sally')
        >>> user.can('edit', thing)
        False

    """
    def wrapper(func):
        def authorize_and_call(self, *args, **kwargs):
            if self.allows(user, action):
                return func(self, *args, **kwargs)
            raise UnauthorizedException('Unauthorized')
        return authorize_and_call
    return wrapper


class View(object):
    """View

    Use to display a model.
    """
    def __call__(self, *a, **k):

        buttons, inputs = remove_buttons(k)

        if len(a):

            view_name = as_attr(a[0])

            if hasattr(self, view_name):
                """Show a specific collection view"""
                result = evaluate(self, view_name, *a[1:], **inputs)

            elif len(a) == 1:
                """Show the default view of an item"""
                try:
                    result = self.show(a[0], **inputs)
                except TypeError, e:
                    error_messages = 'takes exactly', 'got an unexpected'
                    if any(m in e.message for m in error_messages):
                        # if unable to show object with parameters, try
                        # showing without them
                        result = self.show(a[0])
                    else:
                        raise

            elif len(a) > 1:
                result = evaluate(self, a[-1:][0], '/'.join(a[:-1]), **inputs)

            else:
                """No view"""
                result = None
        else:
            """Default collection view"""
            result = evaluate(self, 'index', **inputs)

        if result:
            return result

    def show(self, *a, **k):
        raise PageMissingException


class Controller(object):
    """Controller

    Use this class when an action is going to change the state
    of the model.
    """

    def __call__(self, *a, **k):

        result = None

        buttons, inputs = remove_buttons(k)

        # Buttons
        if buttons:
            button_name = buttons.keys()[0]
            result = evaluate(self, button_name, *a, **inputs)
            if result:
                return result

        method_name = len(a) and as_attr(a[0]) or 'index'

        # Collection methods
        if hasattr(self, method_name):
            result = evaluate(self, method_name, *a[1:], **inputs)

        # Object methods
        elif len(a) > 1:
            method_name = len(a) and as_attr(a[-1:][0])
            result = evaluate(self, method_name, *a[:-1], **inputs)

        # If controller returned a result, we're done
        if result:
            return result


class Dispatcher(object):
    """dispatches actions to a method

    Accepts incoming user input actions and calls the appropriate method to
    handle the request.  Unlike the Controller and the View, the Dispatcher
    doesn't alter the incoming input in any way, but rather passes it along
    verbatim to the method handling the request.

    >>> class MyDispatcher(Dispatcher):
    ...     def add(self, a, b):
    ...         return a + b
    >>> dispatcher = MyDispatcher()
    >>> dispatcher('add', 1, 2)
    3
    """

    def __call__(self, *a, **k):

        method_name = len(a) and as_attr(a[0]) or 'index'

        if hasattr(self, method_name):
            return evaluate(self, method_name, *a[1:], **k)
