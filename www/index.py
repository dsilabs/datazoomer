#!/usr/bin/env python
try:
    try:
        import zoom
        zoom.run()

    except ImportError:
        # Development environment
        import sys, os, imp
        lib_path = os.path.abspath('..')
        sys.path = [lib_path] + sys.path
        import zoom
        zoom.run()

except SystemExit:
    pass

except:
    import traceback
    print 'Content-type: text/html\n\n'
    print '<pre>%s</pre>' % traceback.format_exc()

