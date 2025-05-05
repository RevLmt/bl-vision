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

import os
import json

def save_bboxes_coco_format(bboxes, category_ids, frame_num, image_width, image_height, output_dir):
    """ Saves bounding boxes in COCO JSON format """
    
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "annotations.json")

    image_filename = f"{frame_num:04d}.png"

    # Try to load existing data
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try:
                coco_data = json.load(f)
            except json.JSONDecodeError:
                coco_data = {"images": [], "annotations": [], "categories": []}
    else:
        coco_data = {"images": [], "annotations": [], "categories": []}

    # Check if this image is already added
    image_id = frame_num  # Unique ID based on frame
    if not any(img["id"] == image_id for img in coco_data["images"]):
        coco_data["images"].append({
            "id": image_id,
            "file_name": image_filename,
            "width": image_width,
            "height": image_height
        })

    # Append new bounding boxes
    for i, bbox in enumerate(bboxes):
        min_x, min_y = bbox[0]
        max_x, max_y = bbox[1]
        width = max_x - min_x
        height = max_y - min_y

        annotation_id = len(coco_data["annotations"]) + 1  # Unique annotation ID

        coco_data["annotations"].append({
            "id": annotation_id,
            "image_id": image_id,
            "category_id": category_ids[i],
            "bbox": [min_x, min_y, width, height],  # COCO format [x, y, width, height]
            "area": width * height,
            "iscrowd": 0
        })

    # Save JSON
    with open(json_path, "w") as f:
        json.dump(coco_data, f, indent=4)

    print(f"📄 Saved COCO annotation file: {json_path}")
