"""System wide exceptions"""

class SystemException(Exception): pass
class PageMissingException(Exception): pass
class DatabaseException(Exception): pass
class UnauthorizedException(Exception): pass


class ValidException(Exception):
    """invalid record"""
    pass

class TypeException(Exception):
    """unsupported type"""
    pass

