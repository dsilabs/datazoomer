#!/usr/bin/env python

SYSTEM_ERROR_TEMPLATE = \
        """Content-type: text/html

        <H1>System Error</H1>
        The following error has occured.
        <pre>%s</pre>
        """
try:
    import timeit
    start_time = timeit.default_timer()

    import zoom.startup
    zoom.startup.run(start_time=start_time)

except:
    import traceback
    t = traceback.format_exc()
    print SYSTEM_ERROR_TEMPLATE % t

