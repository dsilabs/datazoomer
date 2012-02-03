#!/usr/bin/env python

try:
    import zoom

except ImportError:
    # dev environment
    import sys, os
    sys.path = [os.path.abspath('..')] + sys.path
    import zoom

zoom.run()
