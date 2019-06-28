'''
Created on Jul 11, 2018

@author: jiankuang
'''

import sys,os;

sys.path.append(os.getcwd() + "/CROW")

import worktools;

if __name__ == '__main__':
#    print("Hello world CROW!")   
    option1 = '-sf'
    casename = 'tutorial_case'
    username = 'casetest1'
    worktools.setup_case([option1,casename,username])
