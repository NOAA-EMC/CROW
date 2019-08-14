#! /usr/bin/env python3.6

import os,sys
import unittest
from context import crow
import crow.config

class TestYamlIO(unittest.TestCase):
	
	def setUp(self):
		self.obj=crow.config.from_file('../test_data/yaml-io/original.yaml')
		self.back2yaml=crow.config.to_yaml(self.obj)
		self.obj2=crow.config.from_string(self.back2yaml)
		self.back2yaml2=crow.config.to_yaml(self.obj2)

	def test_text_match(self):
		self.assertEqual(self.back2yaml, self.back2yaml2)

	def test_obj_match(self):
		self.assertEqual(self.obj, self.obj2)

if __name__ == '__main__':
    unittest.main()
