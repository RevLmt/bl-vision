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
from ..utils.bbox_utils import loop_over_particles, get_filtered_bbox, loop_over_instances_from_selection

class RunMeshBBoxOperator(bpy.types.Operator):
    """Run Mesh Bounding Box Detection"""
    bl_idname = "blv.run_mesh_bbox"
    bl_label = "Run YOLO Mesh BBox"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        bboxes, cat_ids, num_blocked, cat_map, messages = compute_bounding_boxes(scene, include_save=True)
        

        for level, msg in messages:
            self.report({level}, msg)


        if bboxes:
            self.report({'INFO'}, f"✅ Found {len(bboxes)} bounding boxes | Out of View: {num_blocked}")
        else:
            self.report({'WARNING'}, f"⚠️ No bounding boxes detected in frame {scene.frame_current}.")

        return {'FINISHED'}

class RunTestMeshBBoxOperator(bpy.types.Operator):
    bl_idname = "blv.run_test_mesh_bbox"
    bl_label = "Test run of mesh bounding box operator. It will count bboxes for you. Uses raycast if enabled."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        bboxes, cat_ids, num_blocked, cat_map, messages = compute_bounding_boxes(scene, include_save=False)

        for level, msg in messages:
            self.report({level}, msg)

        if bboxes:
            self.report({'INFO'}, f"[TEST] Found {len(bboxes)} bounding boxes | Out of View: {num_blocked}")
        else:
            self.report({'WARNING'}, f"⚠️ [TEST] No bounding boxes detected in frame {scene.frame_current}.")

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


def compute_bounding_boxes(scene, include_save=True):
    """
    Computes 2D bounding boxes for objects in the scene using the active camera.
    Returns:
        bboxes: List of 2D bounding box data
        cat_ids: Corresponding category IDs
        num_blocked: Number of objects filtered out / blocked
        category_mapping: Dict of category_id -> category_name
        objects: List of objects that produced valid bboxes
    """
    cam = scene.camera
    if not cam:
        return [], [], 0, {}, [], [('ERROR', 'Camera not found!')]

    render_res = (scene.render.resolution_x, scene.render.resolution_y)
    bboxes = []
    cat_ids = []
    num_blocked = 0
    category_mapping = {}
    messages = []

    label_dir = scene.blv_save.label_path
    save_bool = include_save and scene.blv_save.bbox_bool
    mode = scene.blv_settings.mode
    formatting = scene.blv_save.format_enum

    use_raycast = scene.blv_settings.raycast_bool
    raycast_method = scene.blv_settings.raycast_enum
    visibility_threshold = scene.blv_settings.visibility_threshold

    if mode == "COLLECTION":
        collection_list = scene.blv_settings.selected_collections
        if not collection_list or not collection_list[0].collection:
            return [], [], 0, {}, [], [('ERROR', 'No valid collection selected!')]

        for col in collection_list:
            cat_id = col.category_id
            category_name = col.collection.name
            category_mapping[cat_id] = category_name
            object_list = col.collection.objects
            include_instances = col.include_instances

            for obj in object_list:
                if obj.type == 'MESH':
                    bbox_2d = get_filtered_bbox(obj, cam, render_res,
                                                use_raycast=use_raycast,
                                                raycast_method=raycast_method,
                                                visibility_threshold=visibility_threshold)
                    if bbox_2d:
                        bboxes.append(bbox_2d)
                        cat_ids.append(cat_id)
                    else:
                        num_blocked += 1

            # Include instances
            if include_instances:
                object_to_cat = {
                    obj: cat_id
                    for obj in object_list
                    if obj is not None and obj.type == 'MESH'
                }

                if object_to_cat:
                    instance_bboxes, instance_cat_ids = loop_over_instances_from_selection(
                        object_to_cat=object_to_cat,
                        cam=cam,
                        scene=scene,
                        min_bbox_size=5,
                        use_raycast=use_raycast,
                        raycast_method=raycast_method,
                        visibility_threshold=visibility_threshold
                    )

                    if instance_bboxes:
                        bboxes.extend(instance_bboxes)
                        cat_ids.extend(instance_cat_ids)
                    else:
                        num_blocked += 1

    elif mode == "OBJECT":
        object_list = scene.blv_settings.selected_objects

        for obj_wrapper in object_list:
            obj = obj_wrapper.object
            cat_id = obj_wrapper.category_id
            category_mapping[cat_id] = obj.name

            if obj and obj.type == 'MESH':
                bbox_2d = get_filtered_bbox(obj, cam, render_res,
                                            use_raycast=use_raycast,
                                            raycast_method=raycast_method,
                                            visibility_threshold=visibility_threshold)
                if bbox_2d:
                    bboxes.append(bbox_2d)
                    cat_ids.append(cat_id)
                else:
                    num_blocked += 1

        # Include instances
        object_to_cat = {
            item.object: item.category_id
            for item in object_list
            if item.include_instances and item.object is not None
        }

        if object_to_cat:
            instance_bboxes, instance_cat_ids = loop_over_instances_from_selection(
                object_to_cat=object_to_cat,
                cam=cam,
                scene=scene,
                min_bbox_size=5,
                use_raycast=use_raycast,
                raycast_method=raycast_method,
                visibility_threshold=visibility_threshold
            )

            if instance_bboxes:
                bboxes.extend(instance_bboxes)
                cat_ids.extend(instance_cat_ids)
            else:
                num_blocked += 1

    elif mode == 'PARTICLE':
        emitter_list = scene.blv_settings.selected_emitter
        

        for emitr in emitter_list:


            part_bboxes, part_cat, part_name = loop_over_particles(emitr, cam, scene,
                                                        use_raycast=use_raycast,
                                                        raycast_method=raycast_method)
            if part_bboxes:
                bboxes.extend(part_bboxes)
                cat_ids.extend(part_cat)
                category_mapping[cat_ids[0]] = part_name[0]

            else:
                num_blocked += 1

    # Save if needed
    if save_bool:
        if formatting == "YOLO":
            generate_yolo_category_files(label_dir, category_mapping)
            save_bboxes_yolo_format(bboxes, cat_ids, scene.frame_current,
                                    render_res[0], render_res[1], label_dir, category_mapping,prefix=scene.blv_save.file_prefix)
        elif formatting == "COCO":
            save_bboxes_coco_format(bboxes, cat_ids, scene.frame_current,
                                    render_res[0], render_res[1], label_dir, prefix=scene.blv_save.file_prefix)

    return bboxes, cat_ids, num_blocked, category_mapping, messages


classes = [
    RunMeshBBoxOperator,
    ChangeRenderDirectoryToFormat,
    RunTestMeshBBoxOperator,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
