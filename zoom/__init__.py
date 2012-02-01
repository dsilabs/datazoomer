#!/usr/bin/env python
"""zoom: manages web apps"""

from __future__ import generators

__version__ = "0.01"
__author__ = [
    "Herb Lainchbury <herb@dynamic-solutions.com>",
    ]
__license__ = "Mozilla Public License 1.1"
__contributors__ = ""

import os
import web
from response import *
from system import System
from config import config

system = System()

def run(system_config_pathname='../sites',force_server_name=None):
    system.run(system_config_pathname)


