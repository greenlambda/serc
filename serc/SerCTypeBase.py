from abc import ABCMeta, abstractmethod
from serc.SerCExceptions import SerCTypeArgsError, SerCParseError

class SerCTypeMeta(ABCMeta):
    """
    The metaclass for all SerC types. It enforces abstract methods and
    registers subclasses of the SerCType parent class.
    """
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'typeRegistry'):
            # This is the base SerC Type class. Create an empty registry
            cls.typeRegistry = {}
        else:
            # This is a derived class, add it the the registry under the name
            # it gives. Error if that name already exists in the registry.
            if not hasattr(cls, 'getTypeID'):
                raise TypeError('All SerCType classes must have a getTypeID function')
            typeID = cls.getTypeID().lower()
            if typeID in cls.typeRegistry:
                raise TypeError('"{2}" failed to register the typeID "{1}", which is already owned by "{0}"'.format(cls.typeRegistry[typeID].__name__, typeID, name))
            cls.typeRegistry[typeID] = cls
            
        super().__init__(name, bases, dct)

class SerCMemberInitialValue(object):
    """Parses initial values of types and holds information about them"""
    def __init__(self, initStr, needsArgument, argumentType=None, argumentName=None):
        """Store things"""
        self.initStr = initStr
        self.needsArgument = needsArgument
        if self.needsArgument:
            self._argumentType = argumentType
            self._argumentName = argumentName

    def parseInitialValue(node, argumentType, argumentName):
        """Creates a new initial value out of a member node"""
        if 'init_value' in node:
            if not isinstance(node['init_value'], dict):
                raise SerCParseError('Initial values must be dictionaries')
            if 'type' not in node['init_value']:
                raise SerCParseError('Initial values must have a type field')

            if node['init_value']['type'].lower() == 'argument':
                return SerCMemberInitialValue(argumentName, True, argumentType, argumentName)
            elif node['init_value']['type'].lower() == 'constant':
                if 'value' not in node['init_value'] or not isinstance(node['init_value']['value'], str):
                    raise SerCParseError('Constant initial values must have a string value field')
                return SerCMemberInitialValue(node['init_value']['value'], False)
        else:
            # Default to argument based initial values
            return SerCMemberInitialValue(argumentName, True, argumentType, argumentName)

    def getArgument(self):
        if self.needsArgument:
            return (self._argumentType, self._argumentName)
        else:
            return None

class SerCType(metaclass=SerCTypeMeta):
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
            if typeNode not in SerCType.typeRegistry:
                raise SerCParseError('Unknown member type: ' + typeNode)
            memberType = SerCType.typeRegistry[typeNode]()
        elif isinstance(typeNode, dict):
            # Full type dictionary
            if 'type_name' not in typeNode:
                raise SerCParseError('Types must have a type name')
            if typeNode['type_name'] not in SerCType.typeRegistry:
                raise SerCParseError('Unknown member type: ' + typeNode['type_name'])
            memberType = None
            if 'args' not in typeNode:
                # No args given, use the defaults
                memberType = SerCType.typeRegistry[typeNode['type_name']]()
            elif isinstance(typeNode['args'], list):
                # There is an args list
                memberType = SerCType.typeRegistry[typeNode['type_name']](*typeNode['args'])
            elif isinstance(typeNode['args'], dict):
                # There is a keyword arg dictionary
                memberType = SerCType.typeRegistry[typeNode['type_name']](**typeNode['args'])
            else:
                # Error parsing the args list
                raise SerCParseError('Unknown type args. Args must be a list or a dictionary')
        else:
            # Types must be strings or type dictionaries
            raise SerCParseError('Types must be strings or type dictionaries')

        # Return the SerCType speced in typeNode
        return memberType

    @abstractmethod
    def getRequiredHeaders(self): pass

    @abstractmethod
    def getRequiredArguments(self): pass

    @abstractmethod
    def formatCType(self): pass

    @abstractmethod
    def formatConstructor(self): pass

    @abstractmethod
    def formatSize(self): pass

    def parse(self, node):
        """
        The parent default parse command that parses basic things common
        to all member variables like names and comments.
        """
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

        self._initValue = SerCMemberInitialValue.parseInitialValue(node, self.formatCType(), self.name)

    def formatDeclaration(self):
        if self.longComment:
           print('    /*\n     * {0}\n     */'.format(self.longComment))
        line = '    {0} {1};'.format(self.formatCType(), self.name)
        if self.inlineComment:
            line += ' /* {0} */'.format(self.inlineComment)
        print(line)
    
