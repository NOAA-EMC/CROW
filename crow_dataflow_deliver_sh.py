#! /usr/bin/env python3.6

import sys, logging, shutil
from getopt import getopt
from contextlib import suppress
from crow.dataflow import Dataflow
from datetime import datetime

ALLOWED_DATE_FORMATS=[ '%Y-%m-%dt%H:%M:%S', '%Y-%m-%dT%H:%M:%S',
                       '%Y-%m-%d %H:%M:%S' ]

def usage(why):
    sys.stderr.write('''Format: crow_dataflow_sh.py [-v] [-m] ( -i input | -o output ) \
  dataflow.db cycle actor var=value [var=value [...]]

  -m = expect multiple matches; -i or -o are formats instead of paths
  -v = verbose (set logging level to logging.DEBUG)
  -i input = local file to deliver to an output slot
  -o output = local file to receive data from an input slot
  dataflow.db = sqlite3 database file with state information
  cycle = forecast cycle in ISO format: 2019-08-15t13:08:14
  actor = actor (job) producing the data (period-separated: path.to.actor)
  slot=slotname = name of slot that produces or consumes the data
''')
    sys.stderr.write(why+'\n')
    exit(1)

def deliver_by_name(flow,local,message):
    if local != '-':
        message.deliver(local)
    elif flow=='I':
        with message.open('rb') as out_fd:
            shutil.copyfileobj(in_fd,sys.stdout)
    elif flow=='O':
        with message.open('wb') as in_fd:
            shutil.copyfileobj(sys.stdin,out_fd)

def deliver_by_format(flow,format,message):
    if "'''" in format:
        raise ValueError(f"{format}: cannot contain three single quotes "
                         "in a row '''")
    globals={ 'actor':message.actor, 'slot':message.slot, 'flow':message.flow, 
              'cycle':message.cycle }
    locals=message.get_meta()
    local_file=eval("f'''"+format+"'''",globals,locals)
    deliver_by_name(local_file,message)

def main():
    (optval, args) = getopt(sys.argv[1:],'o:i:vm')
    options=dict(optval)

    level=logging.DEBUG if optval['v'] else logging.INFO
    logging.basicConfig(stream=sys.stderr,level=level)
    logger=logging.getLogger('crow_dataflow_sh')

    if ( '-i' in options ) == ( '-o' in options ):
        usage('specify exactly one of -o and -i')

    flow = 'I' if '-i' in options else 'O'

    if len(args)<4:
        usage('specify dataflow db file, cycle, actor, and at least one var=value')

    ( dbfile, cyclestr, actor ) = args[0:3]

    for fmt in ALLOWED_DATE_FORMATS:
        with suppress(ValueError):
            cycle=datetime.strptime(cyclestr,fmt)
            break

    slot=None
    meta={}
    for arg in args[3:]:
        split=arg.split('=',1)
        if split!=2:
            usage(f'{arg}: arguments must be var=value')
        ( var, value ) = split
        if var=='slot':
            slot=value
        elif var=='flow':
            usage(f'{arg}: cannot set flow; that is set automatically via -i or -o')
        elif var=='actor':
            usage(f'{arg}: cannot set actor; that is set via a positional argument')
        else:
            meta[var]=value

    db=Dataflow(dbfile)
    if flow=='I':
        matches=iter(db.find_input_slot(actor,slot,meta))
        local=options['-i']
    else:
        matches=iter(db.find_output_slot(actor,slot,meta))
        local=options['-o']

    slot1, slot2 = None, None
    with suppress(StopIteration):
        slot1=found.next()
        slot2=found.next()

    if slot1 is None:
        logger.error('No match.')
        exit(1)

    if slot2 is not None and 'm' not in options:
        logger.error('Multiple matches, and -m not specified.  Abort.')
        exit(1)

    delivery = deliver_by_format if 'm' in options else deliver_by_name

    for slot in [ slot1, slot2 ]:
        if slot is not None:
            deliver(flow,local,slot.at(cycle))
    for slot in matches:
        deliver(flow,local,slot.at(cycle))
