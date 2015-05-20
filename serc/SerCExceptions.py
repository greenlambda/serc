# All the exceptions for serc

class SerCError(Exception):
    """Base class for SerC"""
    pass

class SerCParseError(SerCError):
    """There was an error parsing the JSON file"""
    pass

class SerCTypeArgsError(SerCError):
    """Could not understand one of the arguments to the type"""
    pass
