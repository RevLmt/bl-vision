'''
Copyright (C) 2025 RRX Engineering
http://www.rrxengineering.com

Created by Ryan Revilla

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
import os
from bpy.app.handlers import persistent

home_dir = os.path.expanduser('~')
DEFAULT_SAVE_PATH = os.path.join(home_dir, 'Downloads')



# Properties for data output
class saveDataProperties(bpy.types.PropertyGroup):
    root_path: bpy.props.StringProperty(
        name="Save Path",
        description="Save path for vision data. Changes render save path",
        default=DEFAULT_SAVE_PATH,
        subtype="DIR_PATH",
        update=lambda self, context: toggle_change_render_dir(self, context),
    )
    save_bool: bpy.props.BoolProperty(
        name="Save Data",
        description="Boolean for saving data.",
        default=False,
    )
    format_enum: bpy.props.EnumProperty(
        name="Format",
        description="Vision data format.",
        items=[
            ("YOLO", "YOLO", "Save data in YOLO format"),
            ("COCO", "COCO", "Save data in COCO format"),
        ]
    )
    overwrite_bool: bpy.props.BoolProperty(
        name="Overwrite",
        description="Overwrite",
        default=False,
    )
    bbox_bool: bpy.props.BoolProperty(
        name="Bounding Box",
        description="Output bounding boxes",
        default=False,
        update=lambda self, context: update_handler_and_render_path(self, context),
    )
    segm_bool: bpy.props.BoolProperty(
        name="Segmentation (Coming Soon)",
        description="Output segmentation",
        default=False,
    )
    segm_enum: bpy.props.EnumProperty(
        name="Segmentation Method",
        description="Choose segmentation method",
        items=[
            ("INSTANCE", "Instance", "Save instance segmentation"),
            ("SEMANTIC", "Semantic", "Save semantic (categorical) segmentation"),
        ]
    )
    use_custom_paths: bpy.props.BoolProperty(
        name="Custom Paths",
        description="Enable manual path overrides for images and labels/annotations.",
        default=False,
    )
    custom_image_path: bpy.props.StringProperty(
        name="Custom Image Path",
        subtype="DIR_PATH",
        default="",
        update=lambda self, context: toggle_change_render_dir(self, context),
    )
    custom_label_path: bpy.props.StringProperty(
        name="Custom Label/Annotation Path",
        subtype="DIR_PATH",
        default=""
    )
    file_prefix: bpy.props.StringProperty(
        name="Filename Prefix",
        description="Prefix for images and label filenames",
        default="_",
        update=lambda self, context: toggle_change_render_dir(self, context),
    )
    image_path: bpy.props.StringProperty(
        name="Resolved Image Path",
        subtype="DIR_PATH",
        default=""
    )
    label_path: bpy.props.StringProperty(
        name="Resolved Label/Annotation Path",
        subtype="DIR_PATH",
        default=""
    )
    obb_bool: bpy.props.BoolProperty(
        name="Object-Oriented BBox (Coming Soon)",
        description="Output Object Oriented BBox",
        default=False,
    )
    pose_bool: bpy.props.BoolProperty(
        name="Object Pose (Coming Soon)",
        description="Output object pose information",
        default=False,
    )

####################################
# Functions for handling save paths
####################################
# Utility to resolve dataset paths
def get_dataset_paths(props):
    if props.use_custom_paths:
        return props.custom_image_path, props.custom_label_path

    root = props.root_path
    fmt = props.format_enum

    if fmt == "YOLO":
        return os.path.join(root, "images"), os.path.join(root, "labels")
    elif fmt == "COCO":
        return os.path.join(root, "images"), os.path.join(root, "annotations")
    else:
        return root, root

# Create output folder if it doesn't exist (except for images)
def ensure_label_folder_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"📁 Created directory: {path}")


# set render path and label path
def toggle_change_render_dir(self, context):
    if self.bbox_bool:
        image_path, label_path = get_dataset_paths(self)
        bpy.context.scene.render.filepath = os.path.join(image_path, self.file_prefix)
        self.image_path = image_path
        self.label_path = label_path
        print(f"Render filepath set to: {image_path}")


# handler for calling bbox operator. Should be registered with bpy.app.handlers to be called before each render.
def render_handler(scene):
    props = scene.blv_save
    if props.bbox_bool:
        image_path, label_path = get_dataset_paths(props)
        props.image_path = image_path
        props.label_path = label_path
        ensure_label_folder_exists(label_path)
        print("✅ Running YOLO Bounding Box Operator after render...")
        bpy.ops.blv.run_mesh_bbox()

    if props.segm_bool:
        # Optionally: ensure output folder for segmentation too, if you want
        segm_label_path = props.label_path
        ensure_label_folder_exists(segm_label_path)
        print("✅ Running Segmentation Mask Operator before render...")
        bpy.ops.blv.run_segmentation_mask()

# toggle function for setting pre-render handler. Appends to the render_pre handler.
# Calls the render handler every render.
def toggle_render_handler(self, context):
    if self.bbox_bool:
        if render_handler not in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.append(render_handler)
            print("✅ Pre-render handler registered!")
    else:
        if render_handler in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.remove(render_handler)
            print("❌ Pre-render handler unregistered!")

# persistent function to auto-register render handler
@persistent
def auto_register_handler_on_load(_):
    scene = bpy.context.scene
    print("auto-register called")
    if hasattr(scene, "blv_save") and scene.blv_save.bbox_bool:
        print("re-registering")
        toggle_render_handler(scene.blv_save, bpy.context)

def update_handler_and_render_path(self, context):
    toggle_change_render_dir(self, context)
    toggle_render_handler(self, context)
    

# Save UI Panel
class saveDataPanel(bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_saveDataPanel"
    bl_label = "Data Output"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BL Vision"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        save_props = scene.blv_save

        layout.prop(save_props, "format_enum")
        
        layout.prop(save_props, "bbox_bool")
        col = layout.column()
        col.active = False
        col.prop(save_props, "pose_bool")
        col.prop(save_props, "obb_bool")
        col.prop(save_props, "segm_bool")
        if save_props.bbox_bool:
            layout.prop(save_props, "root_path")
            layout.prop(save_props, "file_prefix")
            layout.prop(save_props, "use_custom_paths")
            if save_props.use_custom_paths:
                layout.prop(save_props, "custom_image_path")
                layout.prop(save_props, "custom_label_path")

            # Display paths without modifying them in draw()
            image_path, label_path = get_dataset_paths(save_props)
            layout.label(text=f"📁 Images: {image_path}")
            layout.label(text=f"📝 Labels/Annotations: {label_path}")


classes = [
    saveDataPanel,
    saveDataProperties,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.blv_save = bpy.props.PointerProperty(type=saveDataProperties)

    if auto_register_handler_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(auto_register_handler_on_load)
        print("📦 Registered load_post handler for bbox_bool")

def unregister():
    if auto_register_handler_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(auto_register_handler_on_load)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.blv_save




if __name__ == "__main__":
    register()