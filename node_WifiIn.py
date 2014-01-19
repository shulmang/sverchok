import bpy
from node_s import *
from util import *


class WifiInNode(Node, SverchCustomTreeNode):
    ''' Wifi Input '''
    bl_idname = 'WifiInNode'
    bl_label = 'Wifi input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    var_name = bpy.props.StringProperty(name = 'var_name', default='a', update=updateNode)
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "var_name", text="var name")
    
    def init(self, context):
        self.inputs.new('StringsSocket', "a[0]", "a[0]")
        
    def check_slots(self, num):
        l = []
        if len(self.inputs) <= num:
            return False
        for i, sl in enumerate(self.inputs[num:]):   
            if len(sl.links) == 0:
                 l.append(i+num)
        if l:
            return l
        else:
            return False


    def update(self):
        global sv_Vars
        # inputs
        ch = self.check_slots(0)
        if ch:
            for c in ch[:-1]:
                self.inputs.remove(self.inputs[ch[-1]])
        
        list_mult=[]
        for idx, multi in enumerate(self.inputs):   
            if multi.links:
                ch = self.check_slots(1)
                if not ch:
                    a_name = self.var_name + '['+str(len(self.inputs))+']'
                    self.inputs.new('StringsSocket', a_name, a_name)
        
        flag_links = False
        for fl in self.inputs:
            if fl.links:
                flag_links = True
                    
        if flag_links:
            self.use_custom_color=True
            self.color = (0.4,0,0.8)
        else:
            self.use_custom_color=True
            self.color = (0.05,0,0.2)
        
        list_vars = []
        for idx, multi in enumerate(self.inputs): 
            a_name = self.var_name + '['+str(idx)+']'
            typ = 's'
            if multi.links:
                if type(multi.links[0].from_socket) == StringsSocket:
                    mult = eval(multi.links[0].from_socket.StringsProperty)
                    typ = 's'
                elif type(multi.links[0].from_socket) == VerticesSocket:
                    mult = eval(multi.links[0].from_socket.VerticesProperty)
                    typ = 'v'
                elif type(multi.links[0].from_socket) == MatrixSocket:
                    mult = eval(multi.links[0].from_socket.MatrixProperty)
                    typ = 'm'
            else:
                mult = [[0.0]]
            
            list_vars.append(mult)
            multi.name = a_name
            sv_Vars['sv_typ'+self.var_name+a_name] = typ
            
        sv_Vars[self.var_name] = list_vars
        
        
     
     
def register():
    bpy.utils.register_class(WifiInNode)
    
def unregister():
    bpy.utils.unregister_class(WifiInNode)

if __name__ == "__main__":
    register()