"""
    site.py

    datazoomer site
"""

class Site(object):

    def __init__(self, name, **kwargs):
        self.name = name
        self.__dict__.update(kwargs)


