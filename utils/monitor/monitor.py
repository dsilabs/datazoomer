"""
    monitor the background queues
"""

from zoom import system


def run():
    def echo(m):
        print(m)
    system.setup()
    system.queues.topic(None).listen(echo, meta=True)

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('\rdone')

