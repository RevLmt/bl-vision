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

        if hit and hit_obj == expected_hit_obj and loc_in_box:
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
    loc_in_box = False
    if bbox is not None:
        loc_in_box = is_point_in_bbox(bbox, loc)
        print("location in box: ",loc_in_box)

    return hit and hit_obj == instance_object and (bbox is None or loc_in_box)


# Experimental convex hull raycast
def raycast_convex_hull(obj, camera, visibility_threshold=0.9, bbox=None):
    # Create a new mesh and object for the convex hull
    mesh = bpy.data.meshes.new(name="ConvexHullMesh")
    hull_obj = bpy.data.objects.new(name="ConvexHull", object_data=mesh)
    bpy.context.collection.objects.link(hull_obj)
    print("Mesh created")

    # Copy the original object's mesh data
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    print("Copied original mesh")

    # Sample points from the convex hull
    sample_points = [hull_obj.matrix_world @ v.co for v in mesh.vertices]

    # Perform raycasting
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    cam_location = camera.matrix_world.translation
    hit_count = 0

    for point in sample_points:
        direction = (point - cam_location).normalized()
        result, location, normal, index, hit_obj, matrix = scene.ray_cast(depsgraph, cam_location, direction)
        if result and hit_obj == obj:
            hit_count += 1

    # Clean up
    bpy.data.objects.remove(hull_obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)

    # Evaluate visibility
    visibility_ratio = hit_count / len(sample_points)
    return visibility_ratio >= visibility_threshold

def raycast_with_bvh(obj, camera, visible_points_world, visibility_threshold, bbox=None):
    """
    Internal helper function for BVH-based visibility testing.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    cam_location = camera.matrix_world.translation

    eval_obj = obj.evaluated_get(depsgraph)
    # eval_obj = obj.evaluated_get(depsgraph)
    try:
        bvh = BVHTree.FromObject(eval_obj, depsgraph, cage=False, epsilon=0.0)
    except Exception as e:
        print(f"⚠️ BVHTree creation failed for {obj.name}: {e}")
        return False

    hits = 0

    for point in visible_points_world:
        direction = (point - cam_location).normalized()
        hit = bvh.ray_cast(cam_location, direction)
        if hit[0] is not None:
            hits += 1

    visibility_ratio = hits / len(visible_points_world)

    return visibility_ratio >= visibility_threshold
    # mesh = eval_obj.to_mesh()
    # if not mesh:
    #     print(f"⚠️ Skipping BVH check — mesh not found for {obj.name}")
    #     return False

    # bvh = BVHTree.FromBMesh(mesh)
    # hits = 0

    # for point in visible_points_world:
    #     direction = (point - cam_location).normalized()
    #     hit = bvh.ray_cast(cam_location, direction)
    #     if hit[0] is not None:
    #         hits += 1

    # eval_obj.to_mesh_clear()
    # visibility_ratio = hits / len(visible_points_world)
    # return visibility_ratio >= visibility_threshold

    
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
            obj_origin = obj.matrix_world @ Vector((0, 0, 0))
            is_visible = raycast_fast(obj_origin, cam, obj)
        if not is_visible:
            return None

    return bbox_2d


def get_particle_2d_bounding_box(particle, mesh_obj, camera_obj, scene,
                                 min_bbox_size=5, use_raycast=False,
                                 raycast_method='fast', visibility_threshold=0.5):
    # Convert mesh bounding box to local corners
    local_bbox_corners = [Vector(corner) for corner in mesh_obj.bound_box]

    # Compute world transform of the particle (position, rotation, scale)
    particle_matrix = Matrix.LocRotScale(
        particle.location,
        particle.rotation,
        Vector.Fill(3, particle.size)
    )

    # Transform local corners to world space at the particle
    corners_world = [particle_matrix @ c for c in local_bbox_corners]
    render_size = (scene.render.resolution_x, scene.render.resolution_y)

    # Project to NDC space
    corners_ndc = project_world_corners_to_ndc(corners_world, camera_obj, scene)

    # Compute 2D bounding box from projected coordinates
    bbox_2d = calculate_bbox_from_ndc(
        corners_ndc, render_size,
        visibility_threshold, min_bbox_size
    )

    if bbox_2d is None:
        return None

    # Optionally verify visibility with raycasting
    if use_raycast:
        
        is_visible = False
        if raycast_method == "accurate":
            is_visible = raycast_accurate(mesh_obj, camera_obj, visibility_threshold, bbox=corners_world, world_matrix=particle_matrix)
        elif raycast_method == "fast":
            is_visible = raycast_fast(particle.location, camera_obj, mesh_obj, bbox=corners_world)
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

        for p in psys.particles:
            bb_2d = get_particle_2d_bounding_box(
                particle=p,
                mesh_obj=instance_obj,
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
