"""
    zoom.groups

    experimental
"""

from zoom.records import Record, RecordStore

from zoom.records import Record, RecordStore


class Group(Record):
    key = property(lambda a: a.groupid)


#class Subgroup(Record):
#    key = property(lambda a: a.groupid, a.subgroupid)
#
#
#class Members(Record):
#    key = property(lambda a: a.userid, a.groupid)
#

class Groups(RecordStore):
    """DataZoomer Groups
    """
    def __init__(self, db):
        RecordStore.__init__(self, db, Group, name='dz_groups', key='groupid')


#class Subgroups(RecordStore):
#    """DataZoomer Subgroups
#    """
#    def __init__(self, db):
#        RecordStore.__init__(self, db, Group, name='dz_subgroups', key=None)
#
#
#class Members(RecordStore):
#    """DataZoomer Members
#    """
#    def __init__(self, db):
#        RecordStore.__init__(self, db, Group, name='dz_members', key=None)
#
