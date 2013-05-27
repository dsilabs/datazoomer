"""
    feature tester
"""

import system
import random
import collections

class Logger:
    entries = []
    def log(self, test, variant, subject):
        self.entries.append((test, variant, subject))


class Selector:
    name = 'stub'
    def __call__(self, subject, variants): pass

class RandomSelector:
    name = 'random'
    def __call__(self, subject, variants):
        random.seed(subject)
        return random.choice(variants.items())


class SubjectProvider:
    """
        Provides a unique id for individual users, whether or not they
        are authenticated.
    """
    def __call__(self):
        return hash(user.is_authenticated and str(user.id) or system.sid)


class Feature:
    """
        Feature

        >>> logger = Logger()
        >>> random.seed(1)
        >>> subjects = [random.random() for x in range(1000)]
        >>> variants = dict(
        ...     one = 'This is variant one',
        ...     two = 'This is variant two',
        ...     three = 'This is variant three',
        ... )
        >>> result = []
        >>> while subjects:
        ...     result.append( Feature('label', variants, subjects.pop, logger=logger).select() )
        >>> result[0]
        ('two', 'This is variant two')
        >>> counter = collections.Counter(entry for entry in logger.entries)
        >>> counter
        Counter({('label', 'three', 'random'): 362, ('label', 'two', 'random'): 330, ('label', 'one', 'random'): 308})

    """

    def __init__(self, name, variants, id_provider=SubjectProvider(), selector=RandomSelector(), logger=Logger()):
        self.name = name
        self.variants = variants
        self.provider = id_provider
        self.logger = logger
        self.selector = selector

    def select(self):
        subject = self.provider()
        variant_name, variant_value = self.selector(subject, self.variants)
        self.logger.log( self.name, variant_name, self.selector.name )
        return variant_name, variant_value


