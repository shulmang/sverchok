# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import bpy
import mathutils
from mathutils import Vector
from bpy.props import StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode, VerticesSocket
from sverchok.data_structure import (updateNode, match_long_cycle)


class SvSetDataObjectNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Set Object Props '''
    bl_idname = 'SvSetDataObjectNode'
    bl_label = 'set_dataobject'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modes = [
        ("location",   "Location(Vec)",   "", 1),
        ("scale",   "Scale(Vec)",   "", 2),
        ("rotation_euler",   "Rotation_Euler(Vec)",   "", 3),
        ("delta_location",   "Delta_Location(Vec)",   "", 4),
        ("delta_scale",   "Delta_Scale(Vec)",   "", 5),
        ("delta_rotation_euler",   "Delta_Rotation_Euler(Vec)",   "", 6),
        ("parent",   "Parent(Obj)",   "", 7),
        ("layers",   "Layers(Int20)",   "", 8),
        ("select",   "Selection(Int)",   "", 9),
        ("custom",   "Custom",   "", 10)
    ]

    formula = StringProperty(name='formula', description='',
                             default='select', update=updateNode)
    Modes = EnumProperty(name="property modes", description="Objects property",
                         default="location", items=modes, update=updateNode)

    def draw_buttons(self, context, layout):
        if self.Modes == 'custom':
            layout.prop(self,  "formula", text="")
        row = layout.row(align=True)
        layout.prop(self, "Modes", "Objects property")

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('SvUndefTypeSocket', 'values')

    def process(self):
        objs = self.inputs['Objects'].sv_get()
        valsoc = self.inputs['values'].sv_get()
        lob = len(objs)

        if self.Modes == 'parent':
            Val = valsoc
            if lob > len(Val):
                objs, Val = match_long_cycle([objs, Val])
        elif self.Modes == 'layers':
            Val = [[True if i > 0 else False for i in valsoc[0]]]
            if lob > len(Val):
                objs, Val = match_long_cycle([objs, Val])
        else:
            Val = valsoc[0]
            if isinstance(Val, (tuple)):
                Val = [Vector(i) for i in Val]
            if lob > len(Val):
                objs, Val = match_long_cycle([objs, Val])

        if self.Modes != 'custom':
            Prop = self.Modes
        else:
            Prop = self.formula

        g = 0
        while g != lob:
            if objs[g] != None:
                exec("objs[g]."+Prop+"= Val[g]")
            g = g+1


def register():
    bpy.utils.register_class(SvSetDataObjectNode)


def unregister():
    bpy.utils.unregister_class(SvSetDataObjectNode)

"""
import parser
import ast
from itertools import chain, repeat
import bpy


import mathutils
from mathutils import Matrix, Vector, Euler, Quaternion, Color

from bpy.props import StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode, VerticesSocket
from sverchok.data_structure import (updateNode, 
                                     SvGetSocketAnyType, match_long_repeat)
from sverchok.utils.sv_itertools import sv_zip_longest

def parse_to_path(p):
    '''
    Create a path and can be looked up easily.
    Return an array of tuples with op type and value
    ops are:
    name - global name to use
    attr - attribute to get using getattr(obj,attr)
    key - key for accesing via obj[key]
    '''
    
    if isinstance(p, ast.Attribute):
        return parse_to_path(p.value)+[("attr", p.attr)] 
    elif isinstance(p, ast.Subscript):
        if isinstance(p.slice.value, ast.Num):
            return  parse_to_path(p.value) + [("key",p.slice.value.n)]
        elif isinstance(p.slice.value, ast.Str):
            return parse_to_path(p.value) + [("key", p.slice.value.s)] 
    elif isinstance(p, ast.Name):
        return [("name", p.id)]
    else:
        raise NameError
        
def get_object(curr_obj, path):
    '''
    access the object speciefed from a path
    generated by parse_to_path
    will fail if path is invalid
    '''
    curr_object = curr_obj
    for t, value in path[1:]:
        if t=="attr":
            curr_object = getattr(curr_object, value)
        elif t=="key":
            curr_object = curr_object[value]
    return curr_object
    
def assign_data(obj, data):
    '''
    assigns data to the object
    '''
    if isinstance(obj, (int, float, str)):
        # doesn't work, catched earlier
        obj = data
    elif isinstance(obj, (Vector, Color)):
        obj[:] = data 
    elif isinstance(obj, (Matrix, Euler, Quaternion)):
        mats = Matrix_generate(data)
        mat = mats[0]
        if isinstance(obj, Euler):
            eul = mat.to_euler(obj.order)
            obj[:] = eul
        elif isinstance(obj, Quaternion):
            quat = mat.to_quaternion()
            obj[:] = quat 
        else: #isinstance(obj, Matrix)
            obj[:] = mat
    else: # super optimistic guess
        obj[:] = type(obj)(data)

bpy_prop_array_cls = None

class SvSetDataObjectNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Set Object Props '''
    bl_idname = 'SvSetDataObjectNode'
    bl_label = 'set_dataobject'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modes = [
        ("location",   "Location",   "", 1),
        ("scale",   "Scale",   "", 2),
        ("rotation_euler",   "Rotation_Euler",   "", 3),
        ("delta_location",   "Delta_Location",   "", 4),
        ("delta_scale",   "Delta_Scale",   "", 5),
        ("delta_rotation_euler",   "Delta_Rotation_Euler",   "", 6),
        ("custom",   "Custom",   "", 7)
    ]

    formula = StringProperty(name='formula',
                             description='property to asign value',
                             default='select', update=updateNode)

    Modes = EnumProperty(name="property modes", description="Objects property",
                         default="location", items=modes, update=updateNode)

    def draw_buttons(self, context, layout):
        if self.Modes == 'custom':
            layout.prop(self,  "formula", text="")
        row = layout.row(align=True)
        layout.prop(self, "Modes", "Objects property")

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('VerticesSocket', 'values').use_prop = True

    def set_bpy_prop_array_cls(self):
        global bpy_prop_array_cls
        if len(bpy.data.objects):
            bpy_prop_array_cls = type(bpy.data.objects[0].layers)

    def process(self):
        if not bpy_prop_array_cls:
            self.set_bpy_prop_array_cls()
        objs = self.inputs['Objects'].sv_get()
        # this is hard because it is hard to inspect data types
        #if isinstance(self.inputs['values'].sv_get(),(tuple)):
        #    Val = [Vector(i) for i in self.inputs['values'].sv_get()[0]]
        #else:
        Val = self.inputs['values'].sv_get()


        if self.Modes != 'custom':
            Prop = self.Modes
            val_iter = iter(Val[0])
            for obj,val in zip(objs, chain(Val[0], repeat(Val[0][-1]))):
                print(obj, Prop, val)
                setattr(obj, Prop, val)
        else:
            ast_path = ast.parse("obj."+self.formula)
            path = parse_to_path(ast_path.body[0].value)    
            for obj,val in sv_zip_longest(objs, Val):
                real_obj = get_object(obj, path)
                print(obj,val,path,real_obj)
                if isinstance(real_obj, (int, float, str, bool, type(None))):
                    if isinstance(real_obj,str):
                        val = str(val)
                    real_obj = get_object(obj, path[:-1])
                    p_type, value = path[-1]
                    if p_type == "attr":
                        setattr(real_obj, value, val)
                    else: 
                        real_obj[value] = val
                elif isinstance(real_obj, (bpy.types.Object, type(None))):
                    print(real_obj, val)
                    real_obj = val
                elif isinstance(real_obj, bpy_prop_array_cls):
                    print(real_obj)
                    for i in range(len(real_obj)):
                        real_obj[i] = val[i]
                else:
                    assign_data(real_obj, val)


        
        while g != len(ObjectID):
            if ObjectID[g] != None:
                exec("ObjectID[g]."+Prop+"= Val[g]")
            g = g+1
        


def register():
    bpy.utils.register_class(SvSetDataObjectNode)


def unregister():
    bpy.utils.unregister_class(SvSetDataObjectNode)

"""
