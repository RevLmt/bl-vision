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

# --------------------------
# Property Groups
# --------------------------

class BBoxSelectionItem(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    emitter_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    category_id: bpy.props.IntProperty(name="Category")


class BBoxTrackingProperties(bpy.types.PropertyGroup):
    mode: bpy.props.EnumProperty(
        name="Detection Mode",
        description="Select whether to track objects or collections",
        items=[
            ('OBJECT', "Object", "Select specific objects"),
            ('COLLECTION', "Collection", "Select entire collections"),
            ('PARTICLE', "Particle Emitter", "Select particle emitter objects")
        ],
        default='COLLECTION'
    )

    selected_objects: bpy.props.CollectionProperty(type=BBoxSelectionItem)
    active_object_index: bpy.props.IntProperty()

    selected_collections: bpy.props.CollectionProperty(type=BBoxSelectionItem)
    active_collection_index: bpy.props.IntProperty()

    selected_emitter: bpy.props.CollectionProperty(type=BBoxSelectionItem)
    active_emitter_index: bpy.props.IntProperty()


# --------------------------
# UI Lists
# --------------------------

class BBOX_UL_ObjectList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "object", text="", emboss=True)
        row.prop(item, "category_id", text="", emboss=True)


class BBOX_UL_CollectionList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "collection", text="", emboss=True)
        row.prop(item, "category_id", text="", emboss=True)


class BBOX_UL_EmitterList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "emitter_obj", text="", emboss=True)
        row.prop(item, "category_id", text="", emboss=True)


# --------------------------
# UI Panel
# --------------------------

class BBOX_PT_TrackingPanel(bpy.types.Panel):
    bl_label = "Mesh Bounding Box Tracking"
    bl_idname = "BBOX_PT_TrackingPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BL Vision"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.blv_settings

        layout.prop(settings, "mode", text="Mode")

        if settings.mode == 'OBJECT':
            col = layout.column()
            col.label(text="Select Objects:")
            header = col.row(align=True)
            header.label(text="Object")
            header.label(text="Category")
            col.template_list("BBOX_UL_ObjectList", "", settings, "selected_objects", settings, "active_object_index")

            row = col.row(align=True)
            row.operator("bbox.add_object", text="Add")
            row.operator("bbox.remove_object", text="Remove")
            col.operator("bbox.auto_assign_categories", text="Auto Assign Categories")
            col.operator("blv.run_yolo_mesh_bbox", text="Test Run Operator")

        elif settings.mode == 'COLLECTION':
            col = layout.column()
            col.label(text="Select Collections:")
            header = col.row(align=True)
            header.label(text="Collection")
            header.label(text="Category")
            col.template_list("BBOX_UL_CollectionList", "", settings, "selected_collections", settings, "active_collection_index")

            row = col.row(align=True)
            row.operator("bbox.add_collection", text="Add")
            row.operator("bbox.remove_collection", text="Remove")
            col.operator("bbox.auto_assign_categories", text="Auto Assign Categories")
            col.operator("blv.run_yolo_mesh_bbox", text="Test Run Operator")

        elif settings.mode == 'PARTICLE':
            col = layout.column()
            col.label(text="Select Particle Emitter Objects:")
            header = col.row(align=True)
            header.label(text="Emitter")
            header.label(text="Category")
            col.template_list("BBOX_UL_EmitterList", "", settings, "selected_emitter", settings, "active_emitter_index")

            row = col.row(align=True)
            row.operator("bbox.add_partsys", text="Add")
            row.operator("bbox.remove_partsys", text="Remove")
            col.operator("bbox.auto_assign_categories", text="Auto Assign Categories")
            col.operator("blv.run_yolo_mesh_bbox", text="Test Run Operator")


# --------------------------
# Category Auto-Assignment Operator
# --------------------------

class BBOX_OT_AutoAssignCategories(bpy.types.Operator):
    bl_idname = "bbox.auto_assign_categories"
    bl_label = "Auto Assign Category IDs"
    bl_description = "Automatically assign category IDs based on item order in list"

    def execute(self, context):
        settings = context.scene.blv_settings

        if settings.mode == 'OBJECT':
            for i, item in enumerate(settings.selected_objects):
                item.category_id = i + 1

        elif settings.mode == 'COLLECTION':
            for i, item in enumerate(settings.selected_collections):
                item.category_id = i + 1

        elif settings.mode == 'PARTICLE':
            for i, item in enumerate(settings.selected_emitter):
                item.category_id = i + 1

        return {'FINISHED'}

# --------------------------
# Operators
# --------------------------

class BBOX_OT_AddObject(bpy.types.Operator):
    bl_idname = "bbox.add_object"
    bl_label = "Add Object"

    def execute(self, context):
        settings = context.scene.blv_settings
        obj = context.object
        if obj and obj.type == 'MESH':
            new_item = settings.selected_objects.add()
            new_item.object = obj
        return {'FINISHED'}



class BBOX_OT_RemoveObject(bpy.types.Operator):
    bl_idname = "bbox.remove_object"
    bl_label = "Remove Object"

    def execute(self, context):
        settings = context.scene.blv_settings
        index = settings.active_object_index
        if 0 <= index < len(settings.selected_objects):
            settings.selected_objects.remove(index)
            settings.active_object_index = max(0, index - 1)
        return {'FINISHED'}


class BBOX_OT_AddCollection(bpy.types.Operator):
    bl_idname = "bbox.add_collection"
    bl_label = "Add Collection"

    def execute(self, context):
        settings = context.scene.blv_settings
        col = context.collection
        if col:
            new_item = settings.selected_collections.add()
            new_item.collection = col
        return {'FINISHED'}


class BBOX_OT_RemoveCollection(bpy.types.Operator):
    bl_idname = "bbox.remove_collection"
    bl_label = "Remove Collection"

    def execute(self, context):
        settings = context.scene.blv_settings
        index = settings.active_collection_index
        if 0 <= index < len(settings.selected_collections):
            settings.selected_collections.remove(index)
            settings.active_collection_index = max(0, index - 1)
        return {'FINISHED'}


class BBOX_OT_AddPartSys(bpy.types.Operator):
    bl_idname = "bbox.add_partsys"
    bl_label = "Add Particle Emitter"

    def execute(self, context):
        settings = context.scene.blv_settings
        obj = context.object
        if obj and obj.type == 'MESH':
            new_item = settings.selected_emitter.add()
            new_item.emitter_obj = obj
        return {'FINISHED'}


class BBOX_OT_RemovePartSys(bpy.types.Operator):
    bl_idname = "bbox.remove_partsys"
    bl_label = "Remove Particle Emitter"

    def execute(self, context):
        settings = context.scene.blv_settings
        index = settings.active_emitter_index
        if 0 <= index < len(settings.selected_emitter):
            settings.selected_emitter.remove(index)
            settings.active_emitter_index = max(0, index - 1)
        return {'FINISHED'}


# --------------------------
# Registration
# --------------------------

classes = [
    BBoxSelectionItem,
    BBoxTrackingProperties,
    BBOX_UL_ObjectList,
    BBOX_UL_CollectionList,
    BBOX_UL_EmitterList,
    BBOX_PT_TrackingPanel,
    BBOX_OT_AddObject,
    BBOX_OT_RemoveObject,
    BBOX_OT_AddCollection,
    BBOX_OT_RemoveCollection,
    BBOX_OT_AddPartSys,
    BBOX_OT_RemovePartSys,
    BBOX_OT_AutoAssignCategories
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.blv_settings = bpy.props.PointerProperty(type=BBoxTrackingProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.blv_settings

if __name__ == "__main__":
    register()



