import bpy
from bpy.types import Operator
from bpy.props import StringProperty, FloatProperty
from bpy_extras.object_utils import AddObjectHelper
from mathutils import Vector
import bmesh
import colorsys

bl_info = {
    "name": "Image To Voxel",
    "author": "Noah Paessel",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > Image Voxel",
    "description": "Adds a new Mesh Object generated from an image",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

class VoxelFactory:
    def __init__(self, imageName, display_size=2, baseScale=1, topScale=0.5):
        self.image = bpy.data.images[imageName]
        self.size = self.image.size
        self.scale = display_size / self.size[0]
        self.topScale = topScale
        self.baseScale = baseScale
        self.offset = self.scale / 2
        self.baseOffset = (self.scale * baseScale) / 2
        self.topOffset = (self.scale * topScale) / 2
        self.collection = bpy.data.collections.new("voxels")
        self.bmesh = bmesh.new()
        self.color_layer = self.bmesh.loops.layers.color.new("v_color")

        bpy.context.scene.collection.children.link(self.collection)

    def get_color(self, x, y):
        stride = self.image.channels
        width = self.size[0]
        index = x * stride + y * stride * width
        return self.image.pixels[index: index + self.image.channels]

    def make_voxel_geom(self, x, y):
        color = self.get_color(x, y)
        red,green,blue,alpha = color
        h,s,l = colorsys.rgb_to_hls(red,green,blue)
        height = l * (10 * self.scale)

        # The Offset points of a rectangular prism:
        x = x * self.scale
        y = y * self.scale
        # Base:
        a = self.bmesh.verts.new((x - self.baseOffset, y - self.baseOffset, 0))
        b = self.bmesh.verts.new((x + self.baseOffset, y - self.baseOffset, 0))
        c = self.bmesh.verts.new((x + self.baseOffset, y + self.baseOffset, 0))
        d = self.bmesh.verts.new((x - self.baseOffset, y + self.baseOffset, 0))

        # Top:
        e = self.bmesh.verts.new((x - self.topOffset, y - self.topOffset, height))
        f = self.bmesh.verts.new((x + self.topOffset, y - self.topOffset, height))
        g = self.bmesh.verts.new((x + self.topOffset, y + self.topOffset, height))
        h = self.bmesh.verts.new((x - self.topOffset, y + self.topOffset, height))

        # The Faces of the rectangular prism:
        fa = self.bmesh.faces.new([a,b,c,d])
        fb = self.bmesh.faces.new([b,f,e,a])
        fc = self.bmesh.faces.new([f,g,h,e])
        fd = self.bmesh.faces.new([g,c,d,h])
        fe = self.bmesh.faces.new([a,e,h,d])
        ff = self.bmesh.faces.new([c,g,f,b])
        for face in (fa, fb, fc, fd, fe, ff):
            for loop in face.loops:
                loop[self.color_layer] = (red,green,blue,1)

    # Create a voxel at the given location.
    # Add it to the scene and to the voxel collection.
    def make_object(self, xx, yy):
        width, height = self.size
        for x in range(width):
            for y in range(height):
                self.make_voxel_geom(x, y)

        mesh = bpy.data.meshes.new("Voxel")
        self.bmesh.to_mesh(mesh)
        mesh.update() # required?
        obj = bpy.data.objects.new("Voxel", mesh)
        obj.location = (xx, yy, 0)
        self.collection.objects.link(obj)
        return obj


class AddImageVoxel(Operator):
    """Create a new Voxel Image Object"""
    bl_idname = "mesh.add_voxel"
    bl_label = "Add Voxel Object"
    bl_options = {'REGISTER', 'UNDO'}


    display_size: bpy.props.FloatProperty(name="Display Size", default=2, min=0.1, max=10)
    voxel_image: bpy.props.StringProperty(name="String Value")

    def execute(self, context):
        voxel_image = self.voxel_image
        vf = VoxelFactory(voxel_image, display_size=2)
        vf.make_object(0, 0)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column()
        col.label(text="Generate Things:")
        col = layout.column()
        col.prop_search(self, "voxel_image", bpy.data, "images")
        col = layout.column()
        col.prop(self, "display_size")

# Only needed if you want to add into a dynamic menu
def menu_func(self, context):
    self.layout.operator(AddImageVoxel.bl_idname, text="Add Voxel Mesh")

def register():
    bpy.utils.register_class(AddImageVoxel)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(AddImageVoxel)

if __name__ == "__main__":
    register()