"""
    users.py

    experimental

    intention is to eventually replace user.py module
"""

from zoom.records import Record, RecordStore

class DzUsers(Record):
    key = property(lambda a: a.userid)
    first_name = property(lambda a: a.firstname)
    last_name = property(lambda a: a.lastname)
    full_name = property(lambda a: a.firstname + a.lastname)
    username = property(lambda a: a.loginid)

User = DzUsers

class UserStore(RecordStore):
    def __init__(self, db):
        RecordStore.__init__(self, db, User)

