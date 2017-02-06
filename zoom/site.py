"""
    site.py

    datazoomer site
"""

class Site(object):

    def __init__(self, name, **kwargs):
        self.name = name
        self.data_path = None
        self.__dict__.update(kwargs)
