"""
    profile.py

    a utility to track down performance issues

    usage:
        watch python profile.py

"""
import cProfile, pstats, StringIO

pr = cProfile.Profile()
pr.enable()

import zoom

pr.disable()
s = StringIO.StringIO()
sortby = 'cumulative'

ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_callers()
print s.getvalue()

