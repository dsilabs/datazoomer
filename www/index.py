#!/usr/bin/env python
import sys, os

lib_path = os.path.abspath('../lib')
sys.path = [lib_path] + sys.path

import zoom
zoom.run()

