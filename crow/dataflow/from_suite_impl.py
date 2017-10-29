import crow.config
from crow.config import Suite, Task
from crow.config import OutputSlot as ConfigOutputSlot
from crow.config import InputSlot as ConfigInputSlot
from crow.dataflow.interface import Dataflow
from crow.tools import typecheck

def _parse_output_slot(actor,slot,sdata):
    meta=dict(sdata)
    if not 'Loc' in meta:
        raise ValueError(f'{actor} {slot}: Must have a Loc entry')
    loc=meta['Loc']
    #typecheck(f'{actor} {slot}: Loc',loc,str)
    del meta['Loc']
    return loc, meta

def _parse_input_slot(actor,slot,sdata):
    meta=dict(sdata)
    if not 'Out' in meta:
        raise ValueError(f'{actor} {slot}: Must have an Out entry')
    out=meta['Out']
    if not out.is_output_slot():
        raise TypeError(f'{actor} {slot}: Out must be a '
                        '!Message for an !OutputSlot')
    del meta['Out']
    return out, meta
    
def _walk_task_tree_for(suite,cls):
    for item in suite.walk_task_tree():
        if isinstance(item.viewed,cls):
            yield item.get_actor_path(),item.get_slot_name(),item

def from_suite(suite,filename):
    typecheck('suite',suite,Suite)
    typecheck('filename',filename,str)
    df=Dataflow(filename)

    # First pass: add output slots:
    for actor, slot, sdata in _walk_task_tree_for(suite,ConfigOutputSlot):
        loc, meta = _parse_output_slot(actor,slot,sdata)
        df.add_output_slot(actor,slot,sdata.get_slot_location(),sdata.get_meta())

    # Second pass: add input slots:
    for actor, slot, sdata in _walk_task_tree_for(suite,ConfigInputSlot):
        islot=df.add_input_slot(actor,slot,sdata.get_meta())
        odata=sdata.get_output_slot()

        found=None
        for oslot in df.find_output_slot(
                odata.get_actor_path(),odata.get_slot_name(),
                odata.get_meta()):
            found=oslot
            break
        if not found: raise ValueError(f'{actor} {slot} output refers to '
                                       'invalid or missing output slot.')
        islot.connect_to(oslot)
    return df


                
