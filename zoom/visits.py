"""
    Visits
"""

import store
import datetime

class Visit(store.Entity): pass

def visited(subject, sid):
    visits = store.store(Visit)
    now = datetime.datetime.now()
    visit = visits.first(session=sid)
    if visit:
        visit.ended = now
        visits.put(visit)
    else:
        visits.put(Visit(session=sid, subject=subject, started=now, ended=now))
