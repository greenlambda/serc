import json
from abc import ABCMeta, abstractmethod


class SerCError(Exception):
    """Base class for SerC"""
    pass

class SerCParseError(SerCError):
    """There was an error parsing the JSON file"""
    pass

class SerCTypeArgsError(SerCError):
    """Could not understand one of the arguments to the type"""
    pass

class SerCType:
    __metaclass__ = ABCMeta
    """
    The base class for all Ser C types.
    """
    @abstractmethod
    def getCType(self): pass

    @abstractmethod
    def parse(self, node): pass

class SerCTypeInt(SerCType):
    """
    This class defines all C integers like int, long, uint8_t, etc.
    """
    VALID_WIDTHS = ['system', 'short', 'long', 8, 16, 32, 64]

    def __init__(self, signedness='signed', width='system'):
        super(SerCTypeInt, self).__init__()
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

    def getCType(self):
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

    def parse(self, node):
        print '    {0} {1}; /* {2} */'.format(self.getCType(), node['name'], node['short_comment'])

class SerCTypeFloat(SerCType):
    """
    This class defines all the C floating point numbers like float or double
    """
    def __init__(self, arg):
        super(SerCTypeFloat, self).__init__()
        self.arg = arg
        

class SerCTypeMallocList(SerCType):
    """
    This class defines all C lists where the lists are malloced.
    """
    def __init__(self, elementTypeNode=u'int'):
        super(SerCTypeMallocList, self).__init__()
        self._elementType = parseMemberType(elementTypeNode)

    def getCType(self):
        return '{0}*'.format(self._elementType.getCType())

    def parse(self, node):
        print '    {0} {1}; /* {2} */'.format(self.getCType(), node['name'], node['short_comment'])

class SerCTypeStructure(SerCType):
    """
    The basic class for a C strucutre.
    """
    def __init__(self, structTypeName):
        super(SerCTypeStructure, self).__init__()
        self._structTypeName = structTypeName

    def getCType(self):
        return 'struct {0}'.format(self._structTypeName)

    def parse(self, node):
        print '    {0} {1}; /* {2} */'.format(self.getCType(), node['name'], node['short_comment'])

TYPE_TABLE = {
    'int': SerCTypeInt,
    'malloc_list': SerCTypeMallocList,
    'struct': SerCTypeStructure
}

def parseMemberType(typeNode):
    """Takes in a SerC type node and parses it into a SerC type class"""
    memberType = None

    # The type can either be a simple string using the defaults or a
    # full type dictionary
    if isinstance(typeNode, basestring):
        # Simple type
        if typeNode not in TYPE_TABLE:
            raise SerCParseError('Unknown member type: ' + typeNode)
        memberType = TYPE_TABLE[typeNode]()
    elif isinstance(typeNode, dict):
        # Full type dictionary
        if 'type_name' not in typeNode:
            raise SerCParseError('Types must have a type name')
        if typeNode['type_name'] not in TYPE_TABLE:
            raise SerCParseError('Unknown member type: ' + typeNode['type_name'])
        memberType = None
        if 'args' not in typeNode:
            # No args given, use the defaults
            memberType = TYPE_TABLE[typeNode['type_name']]()
        elif isinstance(typeNode['args'], list):
            # There is an args list
            memberType = TYPE_TABLE[typeNode['type_name']](*typeNode['args'])
        elif isinstance(typeNode['args'], dict):
            # There is a keyword arg dictionary
            memberType = TYPE_TABLE[typeNode['type_name']](**typeNode['args'])
        else:
            # Error parsing the args list
            raise SerCParseError('Unknown type args. Args must be a list or a dictionary')
    else:
        # Types must be strings or type dictionaries
        raise SerCParseError('Types must be strings or type dictionaries')

    # Return the SerCType speced in typeNode
    return memberType

class JsonToCSerializer(object):
    """
    JsonToCSerializer takes in a file descriptor (anything with
    a .read() method) to JSON formated text containing a description of the
    C structure to create basic serializer/deserializer and basic
    constructor/destructor for.
    """
    def __init__(self, fd):
        super(JsonToCSerializer, self).__init__()
        self._fd = fd
        self._structures = {}
        self._parsedJson = None

    def parse(self):
        """Parse the file into internal state"""
        # Parse the raw JSON
        self._parsedJson = json.load(self._fd)

        # Get out the list of structures and parse each one in turn
        if 'struct_list' not in self._parsedJson or not isinstance(self._parsedJson['struct_list'], list):
            raise SerCParseError('Must must have a structure list')

        # Parse each structure in turn
        for struct in self._parsedJson['struct_list']:
            print 'struct {0};'.format(struct['name'])
        print
        for struct in self._parsedJson['struct_list']:
            self.parseStruct(struct)
            print
        print

    def parseMember(self, node):
        """ Parse a given member variable of a struct in parsed JSON """
        if 'type' not in node:
            raise SerCParseError('All member variables must have a type')

        # Parse the type, then parse the full node into a member
        memberType = parseMemberType(node['type'])
        memberType.parse(node)

    def parseStruct(self, node):
        print 'struct {0} {{'.format(node['name'])
        for elem in node['contents']:
            self.parseMember(elem)
        print '}__attribute__((packed));'
        if 'typedef_name' in node:
            print 'typedef struct {0} {1};'.format(node['name'], node['typedef_name'])


serc = JsonToCSerializer(open('test.json'))
serc.parse()





