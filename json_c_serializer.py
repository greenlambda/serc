import json

class jsonToCSerializer(object):
    """
    jsonToCSerializer takes in a file descriptor (anything with
    a .read() method) to JSON formated text containing a description of the
    C structure to create basic serializer/deserializer and basic
    constructor/destructor for.
    """

    def __init__(self, fd):
        super(jsonToCSerializer, self).__init__()
        self._fd = fd
        self._structures = {}
        self._parsedJson = None

    def _searchJsonObject(self, node):
        """ 
        Recursively search the parsed JSON tree looking for structures to
        mark for later parsing.
        """
        for key in node:
            if key == 'type' and node['type'] == 'struct':
                # Add the structure to the structures list
                if 'name' not in node:
                    raise RuntimeError('Error, all structs must have a name')
                self._structures[node['name']] = node
                print node['name']
            
            # Recursively search the JSON tree for structures
            if isinstance(node[key], list):
                # Check lists first
                for element in node[key]:
                    if isinstance(element, dict):
                        self._searchJsonObject(element)
            elif isinstance(node[key], dict):
                # Then dictionaries
                self._searchJsonObject(element)


    def parse(self):
        """Parse the file into internal state"""
        # Parse the raw JSON
        self._parsedJson = json.load(self._fd)

        # Get out the list of structures and parse each one in turn
        if 'struct_list' not in self._parsedJson or not isinstance(self._parsedJson['struct_list'], list):
            raise RuntimeError('Must must have a structure list')

        #

        # Search the parsed JSON for structures to parse
        self._searchJsonObject(self._parsedJson)

        # Print out some prototypes
        for structName in self._structures:
            print 'struct {0};'.format(structName)
        print
        for structName in self._structures:
            self.parseStruct(self._structures[structName])
            print
        print

    def parseStructNoRecurse(self, node):
        print '    struct {0};'.format(node['name'])

    def parseUint8(self, node):
        print '    uint8_t {0}; /* {1} */'.format(node['name'], node['comment'])

    def parseInt(self, node):
        print '    int {0}; /* {1} */'.format(node['name'], node['comment'])

    def parseDoubleList(self, node):
        print '    double* {0}; /* {1} */'.format(node['name'], node['comment'])

    typeParseTable = {
        'struct': parseStructNoRecurse,
        'uint8_t': parseUint8,  
        'int': parseInt,
        'double_list': parseDoubleList
    }

    def parseNode(self, node):
        nodeType = node['type']
        self.typeParseTable[nodeType](self, node)

    def parseStruct(self, node):
        print 'struct {0} {{'.format(node['name'])
        for elem in node['contents']:
            self.parseNode(elem)
        print '}__attribute__((packed));'
        if 'typedef_name' in node:
            print 'typedef struct {0} {1};'.format(node['name'], node['typedef_name'])


serc = jsonToCSerializer(open('test.json'))
serc.parse()





