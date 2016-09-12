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

from app import App
