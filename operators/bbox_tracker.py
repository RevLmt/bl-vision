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
from ..utils.yolo_bbox import generate_yolo_category_files, save_bboxes_yolo_format
from ..utils.coco_bbox import save_bboxes_coco_format
from ..utils.bbox_utils import loop_over_particles, get_filtered_bbox, loop_over_instances_from_selection, filter_objects_for_instance_selection

class RunMeshBBoxOperator(bpy.types.Operator):
    """Run YOLO Bounding Box Detection"""
    bl_idname = "blv.run_yolo_mesh_bbox"
    bl_label = "Run YOLO Mesh BBox"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        cam = scene.camera
        if not cam:
            self.report({'ERROR'}, "Camera not found!")
            return {'CANCELLED'}

        render_res = (scene.render.resolution_x, scene.render.resolution_y)
        bboxes = []
        cat_ids = []
        num_blocked = 0
        label_dir = scene.blv_save.label_path
        save_bool = scene.blv_save.bbox_bool
        mode = scene.blv_settings.mode
        formatting = scene.blv_save.format_enum
        category_mapping = {}

        use_raycast = scene.blv_settings.raycast_bool
        raycast_method = scene.blv_settings.raycast_enum
        visibility_threshold = scene.blv_settings.visibility_threshold

        if mode == "COLLECTION":
            collection_list = scene.blv_settings.selected_collections
            if not collection_list or not collection_list[0].collection:
                self.report({'ERROR'}, "No valid collection selected!")
                return {'CANCELLED'}

            for col in collection_list:
                cat_id = col.category_id
                category_name = col.collection.name
                category_mapping[cat_id] = category_name

                for obj in col.collection.objects:
                    if obj.type == 'MESH':
                        bbox_2d = get_filtered_bbox(obj, cam, render_res, use_raycast=use_raycast, raycast_method=raycast_method, visibility_threshold=visibility_threshold)
                        if bbox_2d:
                            bboxes.append(bbox_2d)
                            cat_ids.append(cat_id)
                        else:
                            num_blocked += 1

        elif mode == "OBJECT":
            object_list = scene.blv_settings.selected_objects

            for obj_wrapper in object_list:
                obj = obj_wrapper.object
                cat_id = obj_wrapper.category_id
                category_name = obj.name
                category_mapping[cat_id] = category_name

                if obj and obj.type == 'MESH':
                    bbox_2d = get_filtered_bbox(
                        obj,
                        cam,
                        render_res,
                        use_raycast=use_raycast,
                        raycast_method=raycast_method,
                        visibility_threshold=visibility_threshold
                    )
                    if bbox_2d:
                        bboxes.append(bbox_2d)
                        cat_ids.append(cat_id)
                    else:
                        num_blocked += 1

            # ✅ Process instanced versions if checkbox is enabled
            filtered_instance_objs = filter_objects_for_instance_selection(object_list)
            print("Filtered object list: ", filtered_instance_objs)
            if filtered_instance_objs:
                instance_bboxes, instance_cat_ids = loop_over_instances_from_selection(
                    filtered_selection_list=filtered_instance_objs,
                    cam=cam,
                    scene=scene,
                    min_bbox_size=5,
                    use_raycast=use_raycast,
                    raycast_method=raycast_method,
                    visibility_threshold=visibility_threshold
                )
                bboxes.extend(instance_bboxes)
                cat_ids.extend(instance_cat_ids)

            # for obj_wrapper in object_list:
            #     if obj_wrapper.include_instances and obj_wrapper.object:
            #         inst_cat_id = obj_wrapper.category_id
            #         category_mapping[inst_cat_id] = f"{obj_wrapper.object.name} (Instance)"

        elif mode == 'PARTICLE':
            emitter_list = scene.blv_settings.selected_emitter

            for emitr in emitter_list:
                part_bboxes, part_cat = loop_over_particles(emitr, cam, scene, use_raycast=use_raycast, raycast_method=raycast_method)
                bboxes.extend(part_bboxes)
                cat_ids.extend(part_cat)

        if save_bool:
            if formatting == "YOLO":
                generate_yolo_category_files(label_dir, category_mapping)
                save_bboxes_yolo_format(bboxes, cat_ids, scene.frame_current, render_res[0], render_res[1], label_dir, category_mapping)
            elif formatting == "COCO":
                save_bboxes_coco_format(bboxes, cat_ids, scene.frame_current, render_res[0], render_res[1], label_dir)

        if bboxes:
            self.report({'INFO'}, f"✅ Found {len(bboxes)} bounding boxes | Blocked: {num_blocked}")
        else:
            self.report({'WARNING'}, f"⚠️ No bounding boxes detected in frame {scene.frame_current}.")

        return {'FINISHED'}

class RunTestMeshBBoxOperator(bpy.types.Operator):
    bl_idname = "blv.run_test_mesh_bbox"
    bl_label = "Test run of mesh bounding box operator. It will count bboxes for you. Uses raycast if enabled."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        save_settings = context.scene.blv_save
        save_settings.bbox_bool = False
        bpy.ops.blv.run_yolo_mesh_bbox()
        save_settings.bbox_bool = True
        return {'FINISHED'}

class ChangeRenderDirectoryToFormat(bpy.types.Operator):
    bl_idname = "blv.change_render_dir_to_format"
    bl_label = "Change render directory to specified object detection format"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        directory = scene.blv_save.root_path
        img_dir = os.path.join(directory,'images/')
        scene.render.filepath = img_dir
        return {'FINISHED'}


def register():
    bpy.utils.register_class(RunMeshBBoxOperator)
    bpy.utils.register_class(ChangeRenderDirectoryToFormat)
    bpy.utils.register_class(RunTestMeshBBoxOperator)

def unregister():
    bpy.utils.unregister_class(RunMeshBBoxOperator)
    bpy.utils.unregister_class(ChangeRenderDirectoryToFormat)
    bpy.utils.unregister_class(RunTestMeshBBoxOperator)
