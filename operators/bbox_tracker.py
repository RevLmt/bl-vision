
import bpy
import os
from ..utils.yolo_bbox import generate_yolo_category_files, save_bboxes_yolo_format
from ..utils.coco_bbox import save_bboxes_coco_format
from ..utils.bbox_utils import loop_over_particles, get_filtered_bbox

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

        use_raycast = scene.blv_save.raycast_bool
        raycast_method = scene.blv_save.raycast_enum
        visibility_threshold = scene.blv_save.visibility_threshold

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

                if obj.type == 'MESH':
                    bbox_2d = get_filtered_bbox(obj, cam, render_res, use_raycast=use_raycast, raycast_method=raycast_method,visibility_threshold=visibility_threshold)
                    if bbox_2d:
                        bboxes.append(bbox_2d)
                        cat_ids.append(cat_id)
                    else:
                        num_blocked += 1

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



class ChangeRenderDirectoryToFormat(bpy.types.Operator):
    bl_idname = "blv.change_render_dir_to_format"
    bl_label = "Change render directory to specified object detection format"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # setup_render_settings()
        scene = context.scene

        directory = scene.blv_save.root_path
        img_dir = os.path.join(directory,'images/')
        scene.render.filepath = img_dir

        return {'FINISHED'}



def register():
    bpy.utils.register_class(RunMeshBBoxOperator)
    bpy.utils.register_class(ChangeRenderDirectoryToFormat)

def unregister():
    bpy.utils.unregister_class(RunMeshBBoxOperator)
    bpy.utils.unregister_class(ChangeRenderDirectoryToFormat)


