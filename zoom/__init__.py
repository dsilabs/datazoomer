"""
    datazoomer

    web app platform
    https://github.com/dsilabs/datazoomer
    www.datazoomer.com
"""

from __future__ import generators
import warnings as pywarnings

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
from app import App


pywarnings.filterwarnings(
    'ignore',
    '.*the sets module is deprecated.*',
    DeprecationWarning,
    'MySQLdb'
    )


__version__ = "5.0"
__author__ = [
    "Herb Lainchbury <herb@herblainchbury.com>",
]
__license__ = "GNU General Public License (GPL) V3"
__contributors__ = [
    "Sean Hayes <hayes.dsi@gmail.com>",
]
