"""
    buckets

    stores blobs of data
"""

import os
import sys
import uuid
import errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

class Bucket(object):
    """
        >>> from zoom.system import system
        >>> system.setup('../../..')
        >>> path = os.path.join(system.site.data_path, 'buckets')
        >>> ids = ['id_%04d' % (9-i) for i in range(10)]
        >>> new_id = ids.pop

        >>> bucket = Bucket(path, new_id)
        >>> item_id = bucket.put('some data')
        >>> item_id
        'id_0000'
        >>> bucket.get(item_id)
        'some data'
        >>> bucket.exists(item_id)
        True
        >>> bucket.delete(item_id)
        >>> bucket.exists(item_id)
        False

        >>> item_id = bucket.put('%r'%range(10))
        >>> item_id
        'id_0001'
        >>> bucket.exists(item_id)
        True
        >>> bucket.get(item_id)
        '[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]'
        >>> bucket.delete(item_id)

        >>> bucket = Bucket(path, new_id)
        >>> bucket.put('some data')
        'id_0002'
        >>> bucket.put('some more data')
        'id_0003'
        >>> sorted(bucket.keys())
        ['id_0002', 'id_0003']
        >>> for item_id in bucket.keys():
        ...     bucket.delete(item_id)


    """
    def new_id():
        return uuid.uuid4().hex

    def __init__(self, path, id_factory=new_id):
        self.path = os.path.abspath(path)
        self.id_factory = id_factory
        mkdir_p(self.path)

    def put(self, item):
        item_id = self.id_factory()
        pathname = os.path.join(self.path, item_id)
        if os.path.exists(pathname): raise Exception('duplicate item')
        f = open(os.path.join(pathname), 'wb')
        try:
            f.write(item)
        finally:
            f.close()
        return item_id

    def get(self, item_id, default=None):
        pathname = os.path.join(self.path, item_id)
        if not os.path.exists(pathname) and default: return default
        with open(os.path.join(pathname), 'rb') as f:
            return f.read()

    def delete(self, item_id):
        pathname = os.path.join(self.path, item_id)
        os.remove(pathname)

    def exists(self, item_id):
        pathname = os.path.join(self.path, item_id)
        return os.path.exists(pathname)

    def keys(self):
        return os.listdir(self.path)

