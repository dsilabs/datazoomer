
from request import data
from user import user
from exceptions import PageMissingException, UnauthorizedException

__all__ = ['View','Controller','authorize']

def as_attr(text):
    return text.replace('-','_').lower()

def evaluate(o, i, *a, **k):
    name = as_attr(i)
    if hasattr(o, name):
        attr = getattr(o, name)
        if callable(attr):
            try:
                try:
                    return attr(*a, **k)
                except TypeError, e:
                    if 'takes exactly' in e.message or 'got an unexpected' in e.message:
                        return attr()
                    raise
            except:
                if user.is_developer:
                    print 'parameters passed', a, k
                raise
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

class View(object):
    """

        View a model

    """
    def __call__(self, *a, **k):
        
        buttons, inputs = remove_buttons(k)

        if len(a):

            view_name = as_attr(a[0])

            if hasattr(self, view_name):
                """Show a specific collection view"""
                result = evaluate(self, view_name, *a[1:], **inputs)

            elif len(a)==1:
                """Show the default view of an item"""
                try:
                    result = self.show(a[0], **inputs)
                except TypeError, e:
                    if 'takes exactly' in e.message or 'got an unexpected' in e.message:
                        result = self.show(a[0])
                    else:
                        raise

            elif len(a)>1:
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
    """

        Use this class whenever an action is going to change the state of the model.

    """

    def __call__(self, *a, **k):

        result = None

        buttons, inputs = remove_buttons(k)

        #print a, buttons, inputs

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
        elif len(a)>1 :
            method_name = len(a) and as_attr(a[-1:][0])
            result = evaluate(self, method_name, *a[:-1], **inputs)

        # If controller returned a result, we're done
        if result:
            return result            



