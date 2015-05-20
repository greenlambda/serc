from serc.SerCTypeBase import SerCType
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

    def parse(self, node):
        super().parse(node)
        self._initialArgument = (self.formatCType() + ' ' + self.name)
        if 'constructor_value' in node:
            if not isinstance(node['constructor_value'], dict):
                raise SerCParseError('Constructor values must be dictionaries')
            if 'type' not in node['constructor_value']:
                raise SerCParseError('Constructor values must have a type field')
            if node['constructor_value']['type'] == 'argument':
                self._initialArgument = (self.formatCType() + ' ' + self.name)
            elif node['constructor_value']['type'] == 'constant':
                self._initialArgument = None

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

    def formatArgument(self):
        return self._initialArgument

    def formatSize(self):
        return 'sizeof({0})'.format(self.formatCType())

    def formatConstructor(self):
        if self._initialArgument:
            print('    this->{0} = {1};'.format(self.name, self.name))
        else:
            print('    this->{0} = 0;'.format(self.name))

