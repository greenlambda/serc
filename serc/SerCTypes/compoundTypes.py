from serc.SerCTypeBase import SerCType
from serc.SerCExceptions import SerCTypeArgsError, SerCParseError

class SerCTypeVector(SerCType):
    """
    This class defines all C array lists where the lists are malloced. Like C++ vector
    """
    def __init__(self, elementTypeNode='int'):
        super().__init__()
        self._elementType = SerCType.parseTypeNode(elementTypeNode)

    def getTypeID():
        return 'vector'

    def getRequiredHeaders(self):
        """Return the set of required C headers for this type"""
        return {'stdlib.h'}

    def getRequiredArguments(self):
        """
        Returns a list of required arguments for this type. Each
        argument is a tuple of the typestring and the name
        """
        if self._initValue.needsArgument:
            return [self._initValue.getArgument()]
        else:
            return []

    def parse(self, node):
        super().parse(node)
        if 'list_length' not in node:
            raise SerCParseError('Vectors must have a length')

        self.listLength = node['list_length']

    def formatCType(self):
        return '{0}*'.format(self._elementType.formatCType())

    def formatSize(self):
        return '({0} * {1})'.format(self._elementType.formatSize(), self.listLength)

    def formatConstructor(self):
        print('    this->{0} = malloc(sizeof({1}) * {2});'.format(self.name, self._elementType.formatCType(), self.listLength))
        print('    if (this->{0} == NULL) {{'.format(self.name))
        print('        return -1;')
        print('    }')


class SerCTypeStructureStub(SerCType):
    """
    The basic class for a C strucutre stub, that is the reference to
    a structure that one might find inside another structure.
    """
    def __init__(self, structTypeName):
        super(SerCTypeStructureStub, self).__init__()
        self._structTypeName = structTypeName

    def getTypeID():
        return 'struct'

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

    def formatCType(self):
        return 'struct {0}'.format(self._structTypeName)

    def formatSize(self):
        return 'sizeof({0})'.format(self.formatCType())

    def formatConstructor(self):
        print('    {1}_create(&(this->{0}));'.format(self.name, self._structTypeName))

