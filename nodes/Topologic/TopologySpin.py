import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
from . import Replication, ShellByLoft, CellComplexByLoft

def processItem(item):
	wire, \
	origin, \
	x, \
	y, \
	z, \
	degree, \
	sides, \
	tolerance = item
	wires = []
	unit_degree = degree / float(sides)
	for i in range(sides+1):
		wires.append(topologic.TopologyUtility.Rotate(wire, origin, x, y, z, unit_degree*i))
	if wire.IsClosed():
		return CellComplexByLoft.processItem(wires, tolerance)
	else:
		return ShellByLoft.processItem(wires, tolerance)

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvTopologySpin(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Spins the input Wire based on the input number of sides, rotation origin, axis of rotation, and degrees    
	"""
	bl_idname = 'SvTopologySpin'
	bl_label = 'Topology.Spin'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=1, precision=4, update=updateNode)
	Degree: FloatProperty(name="Degree",  default=0, precision=4, update=updateNode)
	Sides: IntProperty(name="Sides", default=16, min=1, update=updateNode)
	Tolerance: FloatProperty(name="Tolerance",  default=0.001, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wire')
		self.inputs.new('SvStringsSocket', 'Origin')
		self.inputs.new('SvStringsSocket', 'X').prop_name = 'X'
		self.inputs.new('SvStringsSocket', 'Y').prop_name = 'Y'
		self.inputs.new('SvStringsSocket', 'Z').prop_name = 'Z'
		self.inputs.new('SvStringsSocket', 'Degree').prop_name = 'Degree'
		self.inputs.new('SvStringsSocket', 'Sides').prop_name = 'Sides'
		self.inputs.new('SvStringsSocket', 'Tolerance').prop_name = 'Tolerance'
		self.outputs.new('SvStringsSocket', 'Topology')

	def process(self):
		originList = []
		if not any(socket.is_linked for socket in self.outputs):
			return
		wireList = self.inputs['Wire'].sv_get(deepcopy=True)
		wireList = Replication.flatten(wireList)
		if (self.inputs['Origin'].is_linked):
			originList = self.inputs['Origin'].sv_get(deepcopy=True)
			originList = Replication.flatten(originList)
		else:
			originList = []
			for aTopology in wireList:
				originList.append(aTopology.CenterOfMass())
		xList = self.inputs['X'].sv_get(deepcopy=True)
		yList = self.inputs['Y'].sv_get(deepcopy=True)
		zList = self.inputs['Z'].sv_get(deepcopy=True)
		degreeList = self.inputs['Degree'].sv_get(deepcopy=True)
		sidesList = self.inputs['Sides'].sv_get(deepcopy=True)
		toleranceList = self.inputs['Tolerance'].sv_get(deepcopy=True)
		xList = Replication.flatten(xList)
		yList = Replication.flatten(yList)
		zList = Replication.flatten(zList)
		degreeList = Replication.flatten(degreeList)
		sidesList = Replication.flatten(sidesList)
		toleranceList = Replication.flatten(toleranceList)
		inputs = [wireList, originList, xList, yList, zList, degreeList, sidesList, toleranceList]
		if ((self.Replication) == "Trim"):
			inputs = Replication.trim(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = Replication.iterate(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = Replication.repeat(inputs)
			inputs = Replication.transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(Replication.interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Topology'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvTopologySpin)

def unregister():
	bpy.utils.unregister_class(SvTopologySpin)
