#!/usr/bin/env python
"""zoom: manages web apps"""

from __future__ import generators

__version__ = "0.01"
__author__ = [
    "Herb Lainchbury <herb@dynamic-solutions.com>",
    ]
__license__ = "Mozilla Public License 1.1"
__contributors__ = ""

import response

def run():
    print response.HTMLResponse('Hello, world.').render()

if __name__ == '__main__':
    run()

