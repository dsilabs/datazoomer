
from utils import threadeddict

class Session(threadeddict):

    def setup(self, db):
        self.username = 'jsmith'


