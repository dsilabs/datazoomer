

from model import *
from zoom.collect import *

class MyView(CollectionView): pass
class MyController(CollectionController): pass

collection = ContactsCollection()
view = MyView(collection)
controller = MyController(collection)

