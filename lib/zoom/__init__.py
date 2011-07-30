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
import system

def run():
    if 'Apache' in os.environ.get('SERVER_SIGNATURE',''):
        system_class = system.ApacheSystem
    else:
        system_class = system.WebpySystem
    s = system_class()
    s.run()

