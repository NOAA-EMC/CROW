import crow.tools
import os.path

## The CONFIG_TOOLS contains the tools available to configuration yaml
## "!calc" expressions in their "tools" variable.
CONFIG_TOOLS=crow.tools.ImmutableMapping({
    'panasas_gb':crow.tools.panasas_gb,
    'gpfs_gb':crow.tools.gpfs_gb,
    'basename':os.path.basename,
    'dirname':os.path.dirname,
    'abspath':os.path.abspath,
    'realpath':os.path.realpath,
    'isdir':os.path.isdir,
    'isfile':os.path.isfile,
    'islink':os.path.islink,
    'exists':os.path.exists,
})
