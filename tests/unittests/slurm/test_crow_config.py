#! /usr/bin/env python3
f'This script requires python 3.6 or later'

import unittest
import datetime
from context import crow
from crow.sysenv import jobs
from collections import OrderedDict

class TestCrowConfig(unittest.TestCase):

    def setUp(self):
        
        self.spec=crow.config.from_file(
            'toy-yaml/test.yml',
            'toy-yaml/platform.yml',
            'toy-yaml/templates.yml',
            'toy-yaml/actions.yml')
        crow.config.validate(self.spec.fcst)
        crow.config.validate(self.spec.test)
        crow.config.validate(self.spec.gfsfcst)

    def test_ordered_dict(self):
        self.assertEqual(self.spec.ordered_dict,OrderedDict([('one',1),('two',2),('three',3),('four',4),('five',5)]))

    def test_set(self):
        self.assertEqual(self.spec.set, set([2, datetime.date(2017, 8, 15), 'a']))

    def test_bool_array(self):
        self.assertEqual(self.spec.fcst.bool_array,[True, False, True])

    def test_int_array(self):
        self.assertEqual(self.spec.fcst.int_array,[1, 2, 3, 4, 5])

    def test_string_array(self):
        self.assertEqual(self.spec.fcst.string_array,['a', 'b', 'c', 'd', 'e'])

if __name__ == '__main__':
    unittest.main()
