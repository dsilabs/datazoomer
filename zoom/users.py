"""
    users.py

    experimental

    intention is to eventually replace user.py module
"""

from zoom.records import Record, RecordStore

class UserRecord(Record):
    key = property(lambda a: a.userid)
    username = property(lambda a: a.loginid)
    first_name = property(lambda a: a.firstname)
    last_name = property(lambda a: a.lastname)
    full_name = property(lambda a: a.firstname + ' ' + a.lastname)

class UserStore(RecordStore):
    """DataZoomer Users

    """
    def __init__(self, db):
        RecordStore.__init__(self, db, UserRecord, name='dz_users', key='userid')
