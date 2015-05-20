import os
import glob
modules = glob.glob(os.path.dirname(__file__)+"/*.py")
__all__ = [ os.path.basename(f)[:-3] for f in modules]

# Construct all of the types so that they get registered
for name in __all__:
    __import__('serc.SerCTypes.{0}'.format(name))

