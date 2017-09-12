#! /usr/bin/env python3.6

import os
import crow.config
import crow.trace

def main():
    conf=crow.config.from_file(os.environ['CONFIG_YAML'])
    namelist=conf.clim_init.namelist
    with open('climatology_init.nl','wt') as fd:
        fd.write(namelist)
    conf.clim_init.command.run()

if __name__=='__main__':
    import trace
    tracer=trace.Trace(ignoredirs=[sys.prefix,sys.exec_prefix],
                       ignoremods=crow.trace.trace_ignore,timing=1)
    tracer.trace('main()')
