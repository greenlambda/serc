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

class SerCType(metaclass=ABCMeta):
    """
    The base class for all SerC types.
    """
    def parseTypeNode(typeNode):
        """Takes in a SerC type node and parses it into a SerC type class"""
        memberType = None

        # The type can either be a simple string using the defaults or a
        # full type dictionary
        if isinstance(typeNode, str):
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

    @abstractmethod
    def getCType(self): pass

    @abstractmethod
    def formatConstructor(self): pass

    def parse(self, node):
        self.longComment = None
        self.inlineComment = None
        if 'long_comment' in node:
            if not isinstance(node['long_comment'], str):
                raise SerCParseError('long_comments must be strings')
            self.longComment = node['long_comment']

        if 'name' not in node or not isinstance(node['name'], str):
            raise SerCParseError('All members must have a name')

        self.name = node['name']

        if 'inline_comment' in node:
            if not isinstance(node['inline_comment'], str):
                raise SerCParseError('inline_comment must be strings')
            self.inlineComment = node['inline_comment']

    def formatDeclaration(self):
        if self.longComment:
           print('    /*\n     * {0}\n     */'.format(self.longComment))
        line = '    {0} {1};'.format(self.getCType(), self.name)
        if self.inlineComment:
            line += ' /* {0} */'.format(self.inlineComment)
        print(line)

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

    def formatConstructor(self):
        print('    this->{0} = 0;'.format(self.name))

class SerCTypeFloat(SerCType):
    """
    This class defines all the C floating point numbers like float or double
    """
    VALID_WIDTHS = ['float', 'double']

    def __init__(self, width='float'):
        super(SerCTypeFloat, self).__init__()
        if width not in self.VALID_WIDTHS:
            raise SerCTypeArgsError('Floating point numbers must be one of the widths: ' + self.VALID_WIDTHS)
        self._width = width

    def getCType(self):
        return self._width

    def formatConstructor(self):
        print('    this->{0} = 0f;'.format(self.name))

    
class SerCTypeMallocList(SerCType):
    """
    This class defines all C lists where the lists are malloced.
    """
    def __init__(self, elementTypeNode='int', length='0'):
        super().__init__()
        self._elementType = SerCType.parseTypeNode(elementTypeNode)
        self._length = length;

    def getCType(self):
        return '{0}*'.format(self._elementType.getCType())

    def parse(self, node):
        super().parse(node)
        if 'list_length' not in node:
            raise SerCParseError('Malloc lists must have a length')

        self.listLength = node['list_length']

    def formatConstructor(self):
        print('    this->{0} = malloc(sizeof({1}) * {2});'.format(self.name, self._elementType.getCType(), self.listLength))


class SerCTypeStructureStub(SerCType):
    """
    The basic class for a C strucutre stub, that is the reference to
    a structure that one might find inside another structure.
    """
    def __init__(self, structTypeName):
        super(SerCTypeStructureStub, self).__init__()
        self._structTypeName = structTypeName

    def getCType(self):
        return 'struct {0}'.format(self._structTypeName)

    def formatConstructor(self):
        print('    {1}_create(&(this->{0}));'.format(self.name, self._structTypeName))

TYPE_TABLE = {
    'int': SerCTypeInt,
    'malloc_list': SerCTypeMallocList,
    'struct': SerCTypeStructureStub,
    'float': SerCTypeFloat
}

class SerCStructure(object):
    """This holds all the data about a structure once it has been parsed"""
    def __init__(self, node):
        """Parse a JSON node into a new object of the SerCStructure class"""
        super(SerCStructure, self).__init__()

        # Do some error checking
        if not isinstance(node, dict):
            raise SerCParseError('Structure definitions must be dictionaries')
        if 'type_name' not in node or not isinstance(node['type_name'], str):
            raise SerCParseError('Structure definitions must have a type_name')
        if 'contents' not in node or not isinstance(node['contents'], list):
            raise SerCParseError('Structures must have a contents list, even if there are no members')

        self.typeName = node['type_name']
        self._members = []
        self.typedefName = None

        for member in node['contents']:
            self._members.append(self.parseMember(member))

        if 'typedef_name' in node:
            if not isinstance(node['typedef_name'], str):
                raise SerCParseError('Structure typedef names must be strings')
            self.typedefName = node['type_name']

    def formatTypedef(self):
        print('typedef struct {0} {1};'.format(self.typeName, self.typedefName))

    def formatPrototype(self):
        print('struct {0};'.format(self.typeName))

    def formatDeclaration(self):
        print('struct {0} {{'.format(self.typeName))
        for member in self._members:
            member.formatDeclaration()
        print('}__attribute__((packed));')

        if self.typedefName:
            self.formatTypedef()

    def formatConstructor(self):
        print('int {0}_create(struct {0}** new) {{'.format(self.typeName))
        print('    *new = malloc(sizeof(struct {0}));'.format(self.typeName))
        print('    struct {0}* this = *new;'.format(self.typeName))
        for member in self._members:
            member.formatConstructor()
        print('    return 0;')
        print('}')

    def parseMember(self, node):
        """ Parse a given member variable of a struct in parsed JSON """
        if 'type' not in node:
            raise SerCParseError('All member variables must have a type')

        # Parse the type, then parse the full node into a member
        memberType = SerCType.parseTypeNode(node['type'])
        memberType.parse(node)
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
        
        # Parse each structure in order
        for structNode in self._parsedJson['struct_list']:
            newStruct = SerCStructure(structNode)
            self._structures[newStruct.typeName] = newStruct

        # Print out structure prototypes
        for structName in self._structures:
            self._structures[structName].formatPrototype()
        print()

        # Print out their definitions
        for structName in self._structures:
            self._structures[structName].formatDeclaration()
        print()

        # Print out their constructors
        for structName in self._structures:
            self._structures[structName].formatConstructor()
        print()

serc = JsonToCSerializer(open('test.json'))
serc.parse()

