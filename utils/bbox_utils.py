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
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import numpy as np
import bmesh
from mathutils.bvhtree import BVHTree

MIN_BBOX_SIZE = 5  # Set a minimum size threshold (in pixels) for bounding boxes


def raycast_accurate(base_obj, camera, visibility_threshold=0.5,bbox=None,
                     *, world_matrix=None, expected_hit_obj=None):
    """
    Perform accurate raycasting to determine visibility.
    Can handle both regular mesh objects and particle instances by optionally providing
    a custom world_matrix and expected_hit_obj.
    """
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    obj_eval = base_obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()

    if world_matrix is None:
        world_matrix = base_obj.matrix_world
    if expected_hit_obj is None:
        expected_hit_obj = base_obj

    cam_location = camera.matrix_world.translation

    obj_origin = world_matrix @ Vector((0, 0, 0))
    view_direction = (obj_origin - cam_location).normalized()

    visible_vertices = []

    for v in mesh.vertices:
        world_pos = world_matrix @ v.co
        to_vertex = world_pos - cam_location

        if to_vertex.dot(view_direction) > 0:
            co_ndc = world_to_camera_view(scene, camera, world_pos)
            if 0.0 <= co_ndc.x <= 1.0 and 0.0 <= co_ndc.y <= 1.0 and co_ndc.z > 0.0:
                visible_vertices.append(world_pos)

    if not visible_vertices:
        obj_eval.to_mesh_clear()
        return False

    visible_count = 0
    for world_pos in visible_vertices:
        direction = (world_pos - cam_location).normalized()
        hit, loc, norm, idx, hit_obj, matrix = scene.ray_cast(depsgraph, cam_location, direction)

        loc_in_box = False
        if bbox is not None:
            loc_in_box = is_point_in_bbox(bbox, loc)
            # print("location in box: ",loc_in_box)

        if hit and hit_obj.name == expected_hit_obj.name and loc_in_box:
            visible_count += 1

    obj_eval.to_mesh_clear()

    visibility_ratio = visible_count / len(visible_vertices)

    return visibility_ratio >= visibility_threshold


def raycast_fast(target_location, camera, instance_object, bbox=None):
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    

    cam_location = camera.matrix_world.translation
    # cam_location = camera.location

    direction = (target_location - cam_location).normalized()

    hit, loc, norm, idx, hit_obj, matrix = scene.ray_cast(depsgraph, cam_location, direction)
    print("raycast hit loc: ", loc)
    print("hit object: ", hit_obj)
    print("desired object: ", instance_object)
    loc_in_box = False
    if bbox is not None:
        loc_in_box = is_point_in_bbox(bbox, loc)
        print("location in box: ",loc_in_box)

    return hit and hit_obj.name == instance_object.name and (bbox is None or loc_in_box)


    
def project_world_corners_to_ndc(corners_world, camera, scene):
    return np.array([
        world_to_camera_view(scene, camera, corner) for corner in corners_world
    ])

def is_point_in_bbox(bbox_world, point_world):
    # takes in bbox corners and a point, both in world space
    
    # calculate min and max XYZ in world space
    min_corner = Vector((
        min(c[0] for c in bbox_world),
        min(c[1] for c in bbox_world),
        min(c[2] for c in bbox_world),
    ))
    max_corner = Vector((
        max(c[0] for c in bbox_world),
        max(c[1] for c in bbox_world),
        max(c[2] for c in bbox_world),
    ))
    
    # Step 4: Check if the point is inside
    return all(min_corner[i] <= point_world[i] <= max_corner[i] for i in range(3))

def calculate_bbox_from_ndc(corners_ndc, render_size, visibility_threshold, min_bbox_size):
    res_x, res_y = render_size

    # Filter for points in front of the camera (positive Z in NDC)
    visible_points = corners_ndc[(corners_ndc[:, 2] > 0)]
    if len(visible_points) <= 3:
        return None

    # Total area covered by projected bounding box (regardless of screen bounds)
    total_rect_min = corners_ndc[:, :2].min(axis=0)
    total_rect_max = corners_ndc[:, :2].max(axis=0)
    total_area = np.prod(total_rect_max - total_rect_min)

    # Clamp visible points to screen space and calculate visible area
    clipped_visible = np.clip(visible_points[:, :2], 0, 1)
    visible_rect_min = clipped_visible.min(axis=0)
    visible_rect_max = clipped_visible.max(axis=0)
    visible_area = np.prod(visible_rect_max - visible_rect_min)

    # Compute how much of the object's projected area is actually visible on screen
    visibility_percentage = (visible_area / total_area) * 100 if total_area > 0 else 0
    if visibility_percentage < visibility_threshold:
        return None

    # Convert NDC coordinates to pixel coordinates
    bbox_2d = []
    for co_2d in corners_ndc:
        x, y, z = co_2d
        pixel_x = x * res_x
        pixel_y = (1 - y) * res_y  # Flip Y-axis for image coordinates
        bbox_2d.append((pixel_x, pixel_y))

    # Clamp to image boundaries
    min_x = max(0, min(p[0] for p in bbox_2d))
    max_x = max(0, min(max(p[0] for p in bbox_2d), res_x))
    min_y = max(0, min(p[1] for p in bbox_2d))
    max_y = max(0, min(max(p[1] for p in bbox_2d), res_y))

    # Filter out very small bounding boxes
    bbox_width = max_x - min_x
    bbox_height = max_y - min_y
    if bbox_width < min_bbox_size or bbox_height < min_bbox_size:
        return None

    return (min_x, min_y), (max_x, max_y)

def get_bbox_center_world(obj):
    # Each corner is in object space, so transform with obj.matrix_world
    bbox_corners_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    # Compute the average of the corners to get the center
    center_world = sum(bbox_corners_world, Vector()) / 8
    return center_world

def get_filtered_bbox(obj, cam, render_resolution, *,min_bbox_size=5,visibility_threshold=0.5, use_raycast=True, raycast_method="accurate"):
    # Get the active scene and object's bounding box corners in world space
    scene = bpy.context.scene
    corners_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    # Project the 3D world-space corners to normalized device coordinates (NDC)
    corners_ndc = project_world_corners_to_ndc(corners_world, cam, scene)

    # Calculate the 2D bounding box from the projected NDC values
    bbox_2d = calculate_bbox_from_ndc(
        corners_ndc, render_resolution,
        visibility_threshold, min_bbox_size
    )

    if bbox_2d is None:
        return None

    # Optionally perform raycasting to confirm visibility
    if use_raycast:
        
        is_visible = False
        if raycast_method == "accurate":
            is_visible = raycast_accurate(obj, cam, visibility_threshold, bbox=corners_world)
        elif raycast_method == "fast":
            # obj_origin = obj.matrix_world @ Vector((0, 0, 0))
            obj_origin = get_bbox_center_world(obj)
            is_visible = raycast_fast(obj_origin, cam, obj)
        if not is_visible:
            return None

    return bbox_2d




def get_instance_2d_bounding_box(matrix_world, instance_obj, camera_obj, scene,
                                 min_bbox_size=5, use_raycast=False,
                                 raycast_method='fast', visibility_threshold=0.5):
    """
    Compute 2D bounding box for a single instanced object given a transform matrix.
    Works for particles, GN instances, and collection instances.
    """
    if instance_obj.type != 'MESH':
        return None

    # Local space bbox
    local_bbox_corners = [Vector(corner) for corner in instance_obj.bound_box]

    # Convert to world space
    corners_world = [matrix_world @ c for c in local_bbox_corners]
    render_size = (scene.render.resolution_x, scene.render.resolution_y)

    # Project to 2D (NDC space)
    corners_ndc = project_world_corners_to_ndc(corners_world, camera_obj, scene)

    # Convert to 2D bbox
    bbox_2d = calculate_bbox_from_ndc(
        corners_ndc, render_size,
        visibility_threshold, min_bbox_size
    )

    if bbox_2d is None:
        return None

    if use_raycast:
        is_visible = False
        if raycast_method == "accurate":
            is_visible = raycast_accurate(instance_obj, camera_obj, visibility_threshold,
                                          bbox=corners_world, world_matrix=matrix_world)
        elif raycast_method == "fast":
            # origin = matrix_world @ Vector((0, 0, 0))
            # obj_origin = get_bbox_center_world(instance_obj)
            obj_origin = sum(corners_world, Vector()) / 8
            print("Target_Location (instance): ", obj_origin)
            print("Target_Location: ", obj_origin)
            is_visible = raycast_fast(obj_origin, camera_obj, instance_obj, bbox=corners_world)
        if not is_visible:
            return None

    return bbox_2d


def loop_over_particles(sel_emitter, cam, scene, *,
                        min_bbox_size=5, use_raycast=False,
                        raycast_method='fast', visibility_threshold=0.5):
    """
    Iterate over particle systems and compute 2D bounding boxes.
    """
    emitter_obj = sel_emitter.emitter_obj
    depsgraph = bpy.context.evaluated_depsgraph_get()
    particle_systems = emitter_obj.evaluated_get(depsgraph).particle_systems

    bboxes = []
    cat_ids = []

    for i, psys in enumerate(particle_systems):
        psys_settings = emitter_obj.particle_systems[i].settings
        cat_id = sel_emitter.category_id
        instance_obj = psys_settings.instance_object

        if not instance_obj:
            continue

        psys_type = psys_settings.type
        print("Type: ", psys_type)

        for p in psys.particles:
            # Compute world transform of the particle (position, rotation, scale)
            
            if psys_type == "HAIR":
                # case for hair system
                particle_matrix = Matrix.LocRotScale(
                    p.hair_keys[0].co,
                    p.rotation,
                    Vector.Fill(3,p.size)
                )
            else:
                # Case for normal particle system
                particle_matrix = Matrix.LocRotScale(
                    p.location,
                    p.rotation,
                    Vector.Fill(3, p.size)
                )
            # compute 2D bounding box
            
            bb_2d = get_instance_2d_bounding_box(
                matrix_world=particle_matrix,
                instance_obj=instance_obj,
                camera_obj=cam,
                scene=scene,
                min_bbox_size=min_bbox_size,
                use_raycast=use_raycast,
                raycast_method=raycast_method,
                visibility_threshold=visibility_threshold
            )
            if bb_2d:
                bboxes.append(bb_2d)
                cat_ids.append(cat_id)

    return bboxes, cat_ids


def filter_objects_for_instance_selection(selection_list):
    """
    Return a filtered list of objects with include_instances enabled.
    """
    return [
        sel_item for sel_item in selection_list
        if sel_item.include_instances and sel_item.object is not None
    ]


def loop_over_instances_from_selection(filtered_selection_list, cam, scene, *,
                                       min_bbox_size=5, use_raycast=False,
                                       raycast_method='fast', visibility_threshold=0.5):
    """
    Iterate over depsgraph instances, matching against a filtered list of original objects
    (with assigned category IDs), and compute bounding boxes.
    Assumes filtering by 'include_instances' was already performed.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bboxes = []
    cat_ids = []

    # Build a lookup from object -> category ID
    object_to_cat = {
        sel_item.object: sel_item.category_id
        for sel_item in filtered_selection_list
        if sel_item.object is not None
    }
    print("Obj to Cat: ", object_to_cat)
    for inst in depsgraph.object_instances:
        if not inst.is_instance:
            print("not instance")
            continue
        print("is instance")

        # Get the source mesh from evaluated instance object
        source_obj = inst.object.evaluated_get(depsgraph)
        print("Source Object: ", source_obj)
        if not source_obj or source_obj.type != 'MESH':
            continue

        # Match source_obj against user-specified originals (by identity or data block)
        matched_cat_id = None
        for match_obj, cat_id in object_to_cat.items():
            if source_obj.original == match_obj or source_obj.data == match_obj.data:
                matched_cat_id = cat_id
                break

        if matched_cat_id is None:
            print("No matched category ID")
            continue
        print("Matched cat id: ", matched_cat_id)

        bb_2d = get_instance_2d_bounding_box(
            matrix_world=inst.matrix_world,
            instance_obj=source_obj,
            camera_obj=cam,
            scene=scene,
            min_bbox_size=min_bbox_size,
            use_raycast=use_raycast,
            raycast_method=raycast_method,
            visibility_threshold=visibility_threshold
        )

        if bb_2d:
            bboxes.append(bb_2d)
            cat_ids.append(matched_cat_id)

    return bboxes, cat_ids




