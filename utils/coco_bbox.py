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

from pathlib import Path
import json

def save_bboxes_coco_format(bboxes, category_ids, frame_num, image_width, image_height, output_dir, prefix=""):
    """ Saves bounding boxes in COCO JSON format """
    
    output_dir = Path(output_dir)
    json_path = output_dir / "train.json"

    # Defensive check: ensure train.json is not a folder
    if json_path.exists() and json_path.is_dir():
        raise ValueError(f"Expected a file path for COCO annotations, but found a directory: {json_path}")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    image_filename = f"{prefix}{frame_num:04d}.png"

    # Try to load existing data
    if json_path.exists():
        with json_path.open("r") as f:
            try:
                coco_data = json.load(f)
            except json.JSONDecodeError:
                coco_data = {"images": [], "annotations": [], "categories": []}
    else:
        coco_data = {"images": [], "annotations": [], "categories": []}

    image_id = frame_num
    if not any(img["id"] == image_id for img in coco_data["images"]):
        coco_data["images"].append({
            "id": image_id,
            "file_name": image_filename,
            "width": image_width,
            "height": image_height
        })

    for i, bbox in enumerate(bboxes):
        min_x, min_y = bbox[0]
        max_x, max_y = bbox[1]
        width = max_x - min_x
        height = max_y - min_y

        annotation_id = len(coco_data["annotations"]) + 1

        coco_data["annotations"].append({
            "id": annotation_id,
            "image_id": image_id,
            "category_id": category_ids[i],
            "bbox": [min_x, min_y, width, height],
            "area": width * height,
            "iscrowd": 0
        })

    # Add categories if missing
    if not coco_data["categories"]:
        unique_cats = sorted(set(category_ids))
        coco_data["categories"] = [{"id": cid, "name": f"class_{cid}"} for cid in unique_cats]

    with json_path.open("w") as f:
        json.dump(coco_data, f, indent=4)

    print(f"📄 Saved COCO annotation file: {json_path}")

