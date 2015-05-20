from serc.SerCTypeBase import SerCType
from serc.SerCExceptions import SerCTypeArgsError, SerCParseError

class SerCTypeFloat(SerCType):
    """
    This class defines all the C floating point numbers like float or double
    """
    VALID_WIDTHS = ['float', 'double']

    def __init__(self, width='float'):
        super().__init__()
        if width not in self.VALID_WIDTHS:
            raise SerCTypeArgsError('Floating point numbers must be one of the widths: ' + self.VALID_WIDTHS)
        self._width = width

    def getTypeID():
        return 'float'

    def formatCType(self):
        return self._width

    def formatArgument(self):
        return (self.formatCType() + ' ' + self.name)

    def formatSize(self):
        return 'sizeof({0})'.format(self.formatCType())

    def formatConstructor(self):
        print('    this->{0} = 0.0f;'.format(self.name))

class SerCTypeDouble(SerCTypeFloat):
    """A convinience class that is just the float type with the width bound to dobule"""
    def __init__(self):
        super().__init__(width='double')

    def getTypeID():
        return 'double'