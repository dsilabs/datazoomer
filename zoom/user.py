
__all__ = ['User']

from utils import threadeddict

class User(threadeddict):

    def setup(self, db, username):
        self.username = username
        self.first_name = 'joe'
        self.last_name = 'smith'

    def get_fullname(self):
        return (self.first_name + ' '  + self.last_name).strip()

    full_name = property(get_fullname)


