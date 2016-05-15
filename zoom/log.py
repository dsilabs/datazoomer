"""
    log.py

    system logger
"""

import os, datetime
from zoom.system import system
from zoom.user import user

class Logger(object):
    """system logger"""

    def __init__(self, asystem):
        """Initialize logger."""
        self.logging = True
        self.system = asystem

    def info(self, message):
        """Log general information about an applicaiton or process."""
        return self.log('I', message)

    def notify(self, **values):
        """Notify processes that an event has occured."""
        import pickle
        message = pickle.dumps(values)
        return self.log('N', message)

    def complete(self, message=''):
        """Log completion of application or process execution."""
        return self.log('C', message)

    def warning(self, message):
        """Log system warning."""
        return self.log('W', message)

    def security(self, message, user_override=None):
        """Log system security warning."""
        return self.log('S', message, username=user_override)

    def error(self, message):
        """Log system error."""
        return self.log('E', message)

    def activity(self, feed, message):
        """Log system error."""
        return self.log('A', message, feed=feed)

    def log(self, status, message, username=None, feed=None):
        """Insert an entry into the system log."""
        # pylint: disable=star-args

        if not self.system.logging:
            return False

        elapsed = self.system.elapsed_time * 1000

        cmd = (
            'insert into log '
            '(app, route, status, user, address, '
            'login, server, timestamp, elapsed, message)'
            'values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        )
        values = [
            self.system.app.name,
            (feed or '/'.join(system.request.route))[:80],
            status,
            username or user.__dict__.get('login_id', 'unknown'),
            os.environ.get('REMOTE_ADDR', ''),
            os.environ.get('LOGNAME', ''),
            self.system.request.server,
            datetime.datetime.now(),
            elapsed,
            message
            ]
        result = self.system.database(cmd, *values)

        return result

def audit(action, subject1, subject2=''):
    """Place an entry in the audit log"""
    now = datetime.datetime.now()
    query = """
        insert into audit_log 
        (app,user,activity,subject1,subject2,timestamp) 
        values (%s,%s,%s,%s,%s,%s)
        """
    system.database(
        query,
        system.app.name,
        user.login_id,
        action,
        subject1,
        subject2,
        now
    )

# pylint: disable=invalid-name
logger = Logger(system)

