"""
    zoom: web app platform (https://github.com/hlainchb/python-zoom)
"""

from __future__ import generators

__version__ = "5.0"
__author__ = [
    "Herb Lainchbury <herb@herblainchbury.com>",
]
__license__ = "GNU General Public License (GPL) V3"
__contributors__ = [
    "Sean Hayes <hayes.dsi@gmail.com>",
]

import imp
import os

from system import system
from user import user

from helpers import *
from request import request, route, data
from fields import *
from tools import *
from log import logger
from mail import send
from page import *
from store import *
from fill import fill
from exceptions import PageMissingException

# legacy models
from storage import Model

import jsonz as json
from mvc import *
from browse import browse

ITEM_MISSING_ERROR = '<H1>Not Found</H1>Unable to locate page.'

import warnings
warnings.filterwarnings('ignore',
    '.*the sets module is deprecated.*',
    DeprecationWarning, 'MySQLdb')

class App:
    def authorized(self):
        return True

    def page_missing(self):
        content = """
        <div class="jumbotron">
            <h1>Page Not Found</h1>
            <p>The page you requested could not be found.  Please contact the administrator or try again.<p>
        </div>
        """
        return page(content)


    def process(self, *route, **data):

        def load_page(module, filler):
            content = load_content(module)
            if content:
                return Page(content, filler)

        system.result = None
        if hasattr(self, 'menu'):
            system.app.menu = self.menu

        if len(route)>1 and os.path.isfile('%s.py'%route[1]) and self.authorized():
            module = route[1]
            a = route[2:]
        else:
            module = 'index'
            a = route[1:]

        filename = '%s.py' % module
        if os.path.isfile(filename):
            source = imp.load_source(module,filename)
            filler     = getattr(source,'filler',None)
            view       = getattr(source,'view',None)
            controller = getattr(source,'controller',None)
        else:
            view = None
            controller = None
            filler = None

        try:
            response = controller and callable(controller) and controller(*a,**data) or view and callable(view) and view(*a,**data)
        except PageMissingException:
            return self.page_missing()

        return response or system.result or load_page(module, filler) or self.page_missing()


    def __call__(self):
        return self.process(*route, **data)


