#! /usr/bin/env python3.6
import logging, os, sys
from datetime import datetime, timedelta
from crow.dataflow import Dataflow


def main():
    logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)

    if os.path.exists('test.db'):
        os.unlink('test.db')
    if os.path.exists('com'):
        shutil.rmtree('com')

    d=Dataflow('test.db')
    
    PRE='com/{cycle:%Y%m%d%H}/{actor}/{slot}.t{cycle:%H}z'
    d.add_output_slot('fam.job1','oslot',PRE+'.x')
    d.add_input_slot('fam.job2','islot')
    d.add_input_slot('fam.job2','tslot',{
        'when':datetime.now(), 'why':True })

    for S in [1,2,3]:
        for L in 'AB':
            d.add_output_slot('fam.job2','oslot',PRE+'.{letter}{slotnum}',
                              {'slotnum':S, 'letter':L})

    for S in [1,2,3]:
        for L in 'AB':
            d.add_input_slot('fam.job3','islot',{'plopnum':S, 'letter':L})

    three_hours=timedelta(seconds=21600)
    for islot in d.find_input_slot('fam.job3','islot'):
        meta=islot.get_meta()
        found=False
        for oslot in d.find_output_slot('fam.job2','oslot',{
                'slotnum':meta['plopnum'], 'letter':meta['letter'] }):
            islot.connect_to(oslot,rel_time=three_hours)

    for cycstr in [ '2017081500', '2017081506', '2017081512' ]:
        d.add_cycle(datetime.strptime(cycstr,'%Y%m%d%H'))

if __name__ == '__main__': 
