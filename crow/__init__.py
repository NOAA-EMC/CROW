import crow._superdebug

version="0.01"

def set_superdebug(val):
    crow._superdebug.superdebug=bool(val)

def get_superdebug(val):
    return crow._superdebug.superdebug
