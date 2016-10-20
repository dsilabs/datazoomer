"""
    zoom.app

    datazoomer app
"""

import imp
from os.path import isfile

from .system import system
from .page import Page
from .tools import load_content
from .exceptions import PageMissingException

# pylint: disable=no-self-use


class App(object):
    """DataZoomer App

    DataZoomer looks in the app.py module for a variable called app that is a
    callable.  In it's simplest form it can be a function but most often it's
    an instance of this object.
    """

    def __init__(self):
        self.menu = []

    def authorized(self):
        """test to see if the user is authorized to run the app

        See mvc.py for more other methods to control access."""
        return True

    def page_missing(self):
        """do this if the requested page is missing"""
        content = """
        <div class="jumbotron">
            <h1>Page Not Found</h1>
            <p>The page you requested could not be found.
            Please contact the administrator or try again.<p>
        </div>
        """
        return Page(content)

    def process(self, *route, **data):
        """process request info"""
        # pylint: disable=star-args

        def load_page(module, filler):
            """load a view page from the current directory"""
            content = load_content(module)
            if content:
                return Page(content, filler)

        def if_callable(method):
            """test if callable and return it or None"""
            return callable(method) and method

        system.result = None
        if self.menu:
            system.app.menu = self.menu

        if len(route) > 1 and isfile('%s.py' % route[1]) and self.authorized():
            module = route[1]
            rest_of_route = route[2:]
        else:
            module = 'index'
            rest_of_route = route[1:]

        filename = '%s.py' % module
        if isfile(filename):
            source = imp.load_source(module, filename)
            app = if_callable(getattr(source, 'app', None))
            view = if_callable(getattr(source, 'view', None))
            controller = if_callable(getattr(source, 'controller', None))
            filler = if_callable(getattr(source, 'filler', None))  # deprecated
        else:
            app = None
            view = None
            controller = None
            filler = None

        try:
            response = \
                    app and app(*rest_of_route, **data) or \
                    controller and controller(*rest_of_route, **data) or \
                    view and view(*rest_of_route, **data)

        except PageMissingException:
            return self.page_missing()

        return (
            response or
            system.result or
            load_page(module, filler) or
            self.page_missing()
        )

    def __call__(self, request):
        # pylint: disable=star-args
        route = request.route
        data = request.data
        return self.process(*route, **data)
