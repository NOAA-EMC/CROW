import logging, sys
from getopt import getopt
from crow.dataflow import Dataflow

def usage(why):
    sys.stderr.write('''Format: crow_dataflow_find_sh.py [-v] (I|O) [ search parameters ]
 -v = verbose
 I = input slot
 O = output slot
 actor=path.to.actor = actor producing or consuming data
 slot=slot_name = name of input or output slot
 other=other = slot property''')
    sys.stderr.write(why+'\n')
    exit(1)

def main():
    (optval,args) = getopt(sys.argv[1:],'v')
    options=dict(optval)
    if len(args)<2):
        usage('specify database file and flow')

    level=logging.DEBUG if optval['v'] else logging.INFO
    logging.basicConfig(stream=sys.stderr,level=level)
    logger=logging.getLogger('crow_dataflow_sh')

    dbfile, flow = args[0:2]

    if flow not in 'OI':
        usage("flow must be O (output) or I (input)")

    primary={ 'flow':flow, 'actor':None, 'slot':None }
    meta={}
    for arg in args[2:]:
        split=arg.split('=',1)
        if split!=2:
            usage(f'{arg}: arguments must be var=value')
        ( var, value ) = split
        if var in primary:
            primary[var]=value
        else:
            meta[var]=value

    db=Datflow(dbfile)
    find=db.find_output_slot if flow=='O' else db.find_input_slot

    for slot in find(actor,slot,meta):
        meta=slot.get_meta()
        if meta:
            metas=[ f'{k}={v}' for k,v in meta.items() ]
            print(f'{slot.flow} {slot.actor} {slot.slot} {" ".join(metas)}')
        else:
            print(f'{slot.flow} {slot.actor} {slot.slot}')
