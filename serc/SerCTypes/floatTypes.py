from serc.SerCTypeBase import SerCType, SerCMemberInitialValue
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

    def getRequiredHeaders(self):
        """Return the set of required C headers for this type"""
        return set()

    def getRequiredArguments(self):
        """
        Returns a list of required arguments for this type. Each
        argument is a tuple of the typestring and the name
        """
        if self._initValue.needsArgument:
            return [self._initValue.getArgument()]
        else:
            return []

    def getTypeID():
        return 'float'

    def formatCType(self):
        return self._width

    def formatSize(self):
        return 'sizeof({0})'.format(self.formatCType())

    def formatConstructor(self):
        print('    this->{0} = {1};'.format(self.name, self._initValue.initStr))

class SerCTypeDouble(SerCTypeFloat):
    """A convinience class that is just the float type with the width bound to dobule"""
    def __init__(self):
        super().__init__(width='double')

    def getTypeID():
        return 'double'