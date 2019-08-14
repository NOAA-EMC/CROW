#! /usr/bin/env python3
import unittest
from context import crow
import os
import crow.config
from datetime import timedelta, date, datetime
from collections import OrderedDict
from crow.metascheduler import to_ecflow

class TestEcFlowTaskarray(unittest.TestCase):

    def setUp(self):
        self.conf=crow.config.from_file('../test_data/taskarray/taskarray.yaml')
        self.suite=crow.config.Suite(self.conf.suite)
        self.ecflow_suite = to_ecflow(self.suite)
        safe,self.name,self.ecf_files,self.suite_defs = self.ecflow_suite.each_suite()
        for defname in self.suite_defs:
            filename=defname
            print(filename)
            dirname=os.path.dirname(filename)
            if dirname and not os.path.exists(dirname):
                os.makedirs(os.path.dirname(filename))
            with open(filename,'wt') as fd:
                fd.write(self.suite_defs[defname])
#
#        for setname in self.ecf_files:
#            for filename in ecf_files[setname]:
#                print(f'  file {filename}')
#                dirname=os.path.dirname(filename)
#                if dirname and not os.path.exists(dirname):
#                    os.makedirs(os.path.dirname(filename))
#                with open(filename+".ecf",'wt') as fd:
#                    fd.write(ecf_files[setname][filename])
#
    def test_not_working_ec(self):
        print(self.ecflow_suite.each_suite())
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
