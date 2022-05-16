import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def repeat(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
			# print(base,y)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def lace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in lace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

def processItem(item):
	vertex = item[0]
	face = item[1]
	projected_vertex = None
	if vertex and face:
		if (face.Type() == topologic.Face.Type()) and (vertex.Type() == topologic.Vertex.Type()):
			projected_vertex = (topologic.FaceUtility.ProjectToSurface(face, vertex))
	return projected_vertex

lacing = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Lace", "Lace", "", 5)]

class SvVertexProject(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs True if the input Vertex is inside the input Face. Returns False otherwise
	"""
	bl_idname = 'SvVertexProject'
	bl_label = 'Vertex.Project'
	Lacing: EnumProperty(name="Lacing", description="Lacing", default="Default", items=lacing, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Vertex')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Lacing",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertexList = self.inputs['Vertex'].sv_get(deepcopy=False)
		faceList = self.inputs['Face'].sv_get(deepcopy=False)
		faceList = flatten(faceList)
		inputs = [vertexList, faceList]
		if ((self.Lacing) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Lacing) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Lacing) == "Repeat") or ((self.Lacing) == "Default"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Lacing) == "Lace"):
			inputs = list(lace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvVertexProject)

def unregister():
	bpy.utils.unregister_class(SvVertexProject)
