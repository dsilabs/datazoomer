#!/usr/bin/env python

try:
    import zoom.platform

except ImportError:
    # dev environment
    import sys, os
    sys.path = [os.path.abspath('..')] + sys.path
    import zoom.platform

zoom.platform.run()

