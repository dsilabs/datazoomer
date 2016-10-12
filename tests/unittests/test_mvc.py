"""
    Test the mvc module

    Copyright (c) 2005-2012 Dynamic Solutions Inc. (support@dynamic-solutions.com)

    This file is part of DataZoomer.
"""

import os, unittest

from zoom.mvc import evaluate, View, Controller, Dispatcher

class TestEvaluate(unittest.TestCase):

    class MyView(object):

        v1 = 'avalue'

        def f1(self):
            return 'done'

        def f1a(self):
            def f():
                return 'x'
            return f('unexpected')

        def f1b(self, key, **kwargs):
            def f(t, n):
                return 'x'
            return f(key)

        def f2(self, *args, **kwargs):
            return args, kwargs

        def f3(self, key, *args, **kwargs):
            return key, args, kwargs
    view = MyView()

    def test_evaluate(self):
        view = self.view
        self.assertEqual(evaluate(view, 'v1'), 'avalue')
        self.assertEqual(evaluate(view, 'f1'), 'done')
        self.assertEqual(evaluate(view, 'f2', 'akey'), (('akey',), {}))
        self.assertEqual(evaluate(view, 'f3', 'akey'), ('akey', (), {}))

    def test_missing_parameters(self):
        with self.assertRaises(TypeError):
            evaluate(self.view, 'f3')

    def test_legacy_parameterless_method(self):
        #with self.assertRaises(TypeError):
        #    evaluate(self.view, 'f1', 'key', name='test')
        self.assertEqual(evaluate(self.view, 'f1', 'key', name='test'), 'done')

    def test_legacy_parameterless_method(self):
        self.assertEqual(evaluate(self.view, 'f1', 'key', name='test'), 'done')
        with self.assertRaises(TypeError):
            evaluate(self.view, 'f1a', 'key', name='test')
        with self.assertRaises(TypeError) as e:
            evaluate(self.view, 'f1b', 'key', name='test')
        # make sure we're reporting the offending call
        self.assertEqual(str(e.exception)[:9], 'f() takes')
