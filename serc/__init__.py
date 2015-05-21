import json, itertools
from serc.SerCExceptions import SerCTypeArgsError, SerCParseError
from serc.SerCTypeBase import SerCType

# Import all the types. This also registers all of the types
import serc.SerCTypes

def _formatArgument(arg):
    return (arg[0] + ' ' + arg[1])

class SerCStructure(object):
    """This holds all the data about a structure once it has been parsed"""
    def __init__(self, node):
        """Parse a JSON node into a new object of the SerCStructure class"""
        super().__init__()

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
            self.typedefName = node['typedef_name']

    def getRequiredHeaders(self):
        """
        Get all the required headers for this structure, which is the
        union of all the required headers for the members plus
        string.h for memcpy.
        """
        requiredHeaders = {'string.h'}
        for member in self._members:
            requiredHeaders = requiredHeaders.union(member.getRequiredHeaders())
        return requiredHeaders

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

    def formatSize(self):
        print('size_t {0}_size(struct {0}* this) {{'.format(self.typeName))
        print('    return ({0});'.format(' + '.join(member.formatSize() for member in self._members)))
        print('}')

    def formatAllocate(self):
        allocStr = """ssize_t {0}_allocate(struct {0}** block) {{
    *block = malloc(sizeof(struct {0}));
    if (*block == NULL) {{
        return -1;
    }}
    return sizeof(struct {0});
}}
""".format(self.typeName)
        print(allocStr)

    def formatConstructor(self):
        args = itertools.chain([('struct {0}*'.format(self.typeName), 'this')], itertools.chain.from_iterable(member.getRequiredArguments() for member in self._members))
        argsStr = map(_formatArgument, args)
        print('int {0}_construct({1}) {{'.format(self.typeName, ', '.join(argsStr)))
        for member in self._members:
            member.formatConstructor()
        print('    return 0;')
        print('}')

    def formatNew(self):
        args = itertools.chain([('struct {0}*'.format(self.typeName), 'this')], itertools.chain.from_iterable(member.getRequiredArguments() for member in self._members))
        argsStr = map(_formatArgument, args)
        rawArgs = itertools.chain.from_iterable(member.getRequiredArguments() for member in self._members)
        constructorArgsStr = map(lambda arg: arg[1], rawArgs)
        newStr = """ssize_t {0}_new({1}) {{
    ssize_t alloc_ret = {0}_allocate(this_ptr);
    if (alloc_ret < 0) {{
        return -1;
    }}
    if ({0}_construct(*this_ptr, {2}) < 0) {{
        return -1;
    }}
    return alloc_ret;
}}
""".format(self.typeName, ', '.join(argsStr), ', '.join(constructorArgsStr))
        print(newStr)

    def formatSerializer(self):
        print('int {0}_serialize(uint8_t* buffer, int max_length, struct {0}* this) {{'.format(self.typeName))
        print('    size_t offset = 0;')
        for member in self._members:
            print('    memcpy(&(this->{0}), &(buffer[offset]), {1});'.format(member.name, member.formatSize()))
            print('    offset += {0};'.format(member.formatSize()))
            print()
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
        super().__init__()
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

        # Format and print the required headers
        requiredHeaders = set()
        for structName in self._structures:
            requiredHeaders = requiredHeaders.union(self._structures[structName].getRequiredHeaders())
        for header in requiredHeaders:
            print('#include <{0}>'.format(header))
        print()

        # Print out structure prototypes
        for structName in self._structures:
            self._structures[structName].formatPrototype()
        print()

        # Print out their definitions
        for structName in self._structures:
            self._structures[structName].formatDeclaration()
            print()
        print()

        # Print out their length functions
        for structName in self._structures:
            self._structures[structName].formatSize()
            print()
        print()

        # Print out their allocators
        for structName in self._structures:
            self._structures[structName].formatAllocate()
            print()
        print()

        # Print out their constructors
        for structName in self._structures:
            self._structures[structName].formatConstructor()
            print()
        print()

        # Print out their new functions
        for structName in self._structures:
            self._structures[structName].formatNew()
            print()
        print()

        # Print out their serializers
        for structName in self._structures:
            self._structures[structName].formatSerializer()
            print()
        print()


