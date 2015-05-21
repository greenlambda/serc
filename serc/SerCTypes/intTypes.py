from serc.SerCTypeBase import SerCType, SerCMemberInitialValue
from serc.SerCExceptions import SerCTypeArgsError, SerCParseError

class SerCTypeInt(SerCType):
    """
    This class defines all C integers like int, long, uint8_t, etc.
    """
    VALID_WIDTHS = ['system', 'short', 'long', 8, 16, 32, 64]

    def __init__(self, signedness='signed', width='system'):
        super().__init__()
        # Parse the signedness
        if signedness == 'unsigned':
            self._isSigned = False
        elif signedness == 'signed':
            self._isSigned = True
        else:
            raise SerCTypeArgsError('Integers must be either signed or unsigned')

        # Parse the bit width
        if width not in self.VALID_WIDTHS:
            raise SerCTypeArgsError('Integers must be of one of the widths: ' + str(self.VALID_WIDTHS))
        self._width = width

    def getTypeID():
        return 'int'

    def getRequiredHeaders(self):
        """Return the set of required C headers for this type"""
        if not isinstance(self._width, str):
            return {'stdint.h'}
        else:
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

    def formatCType(self):
        if self._width == 'system':
            if self._isSigned:
                return 'int'
            else:
                return 'unsigned int'
        elif self._width == 'short':
            if self._isSigned:
                return 'short'
            else:
                return 'unsigned short'
        elif self._width == 'long':
            if self._isSigned:
                return 'long'
            else:
                return 'unsigned long'
        else:
            prefix = ''
            if not self._isSigned:
                prefix = 'u'
            return '{0}int{1}_t'.format(prefix, self._width)

    def formatSize(self):
        return 'sizeof({0})'.format(self.formatCType())

    def formatConstructor(self):
        print('    this->{0} = {1};'.format(self.name, self._initValue.initStr))

class SerCTypeUint8(SerCTypeInt):
    """A simple binding of the Int type for uint8_t"""
    def __init__(self):
        super().__init__(signedness='unsigned', width=8)

    def getTypeID():
        return "uint8_t"
        
