#! /usr/bin/env python3.6

import os
import sys
import shutil
import crow.config
import crow.trace

def main():
    conf=crow.config.from_file(os.environ['CONFIG_YAML'])
    scope_name=sys.argv[1]
    scope=conf[scope_name]
    
    def run_fcst(action):
        namelist=action.namelist
        with open('forecast.nl','wt') as fd:
            fd.write(namelist)
        action.command.run()
    
    if len(sys.argv)>=3:
        start_member=int(sys.argv[2],10)
        stop_member=int(sys.argv[3],10)
        member_id=start_member
        while member_id<=stop_member:
            fcst=copy(scope)
            fcst.member_id=member_id
            run_fcst(fcst)
            result=fcst.end_result
            shutil.copy2(result,os.path.join(fcst.com,result))
            member_id+=1
    else:
        run_fcst(scope)

if __name__=='__main__':
    import trace
    tracer=trace.Trace(ignoredirs=[sys.prefix,sys.exec_prefix],
                       ignoremods=crow.trace.trace_ignore,timing=1)
    tracer.trace('main()')
