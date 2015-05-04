import json


def parseStruct(node):
	print 'struct {0} {{'.format(node['name'])
	for elem in node['contents']:		w	IHQtOI
		parseNode(elem)
	print '}__attribute__((packed));'
	if 'typedef_name' in node:
		print 'typedef struct {0} {1};'.format(node['name'], node['typedef_name'])


def parseUint8(node):
	print '    uint8_t {0}; /* {1} */'.format(node['name'], node['comment'])

def parseDoubleList(node):
	print '    double* {0}; /* {1} */'.format(node['name'], node['comment'])

typeParseTable = {
	'struct': parseStruct,
	'uint8_t': parseUint8,
	'double_list': parseDoubleList
}

def parseNode(node):
	typeParseTable[node['type']](node)


testText = open('test.json').read()
structData = json.loads(testText)
parseNode(structData)



