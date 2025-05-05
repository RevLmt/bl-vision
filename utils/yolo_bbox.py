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


###
# Data formatting and saving
###

def save_bboxes_yolo_format(bboxes, category_ids, frame_num, image_width, image_height, output_dir, category_mapping):
    """ Saves bounding boxes in YOLO format and generates category files """

    os.makedirs(output_dir, exist_ok=True)
    label_file = os.path.join(output_dir, f"{frame_num:04d}.txt")

    if not bboxes:
        print(f"⚠️ No valid bboxes for frame {frame_num}. Skipping file.")
        with open(label_file, "w") as f:
            pass  # Create an empty label file for completeness
        return

    # Write YOLO annotation file
    with open(label_file, "w") as f:
        for i, bbox in enumerate(bboxes):
            (min_x, min_y), (max_x, max_y) = bbox

            # Normalize bbox values (YOLO format: x_center, y_center, width, height)
            x_center = ((min_x + max_x) / 2) / image_width
            y_center = ((min_y + max_y) / 2) / image_height
            width = (max_x - min_x) / image_width
            height = (max_y - min_y) / image_height

            f.write(f"{category_ids[i]} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

    print(f"📄 Saved YOLO annotation file: {label_file}")

  

def generate_yolo_category_files(output_dir, category_mapping):
    """Generates YOLO category files: `data.yaml` (Ultralytics-style)."""

    yaml_path = os.path.join(output_dir, "data.yaml")
    write_ultralytics_yaml(
        output_path=yaml_path,
        dataset_root=output_dir,
        train_dir="images/train",
        val_dir="images/val",
        category_mapping=category_mapping  # real ID mapping
    )
    print(f"📄 Saved YOLO data config file: {yaml_path}")



# simple method for writing yolo yaml file
def write_yolo_config_yaml(path, train_path, val_path, class_names):
    with open(path, 'w') as f:
        f.write(f"train: {train_path}\n")
        f.write(f"val: {val_path}\n")
        f.write("names:\n")
        for i, name in enumerate(class_names):
            f.write(f"  {i}: {name}\n")

# method for writing yolo ultralytics format yaml file
def write_ultralytics_yaml(
    output_path,
    dataset_root="../dataset",  # base folder, relative or absolute
    train_dir="images/train",
    val_dir="images/val",
    test_dir=None,  # optional
    category_mapping=None  # dict like {12: 'apple', 15: 'banana'}
):
    if category_mapping is None:
        category_mapping = {}

    with open(output_path, "w") as f:
        f.write(f"path: {dataset_root}\n")
        f.write(f"train: {train_dir}\n")
        f.write(f"val: {val_dir}\n")
        if test_dir:
            f.write(f"test: {test_dir}\n")
        f.write("names:\n")
        for cid in sorted(category_mapping.keys()):
            f.write(f"  {cid}: {category_mapping[cid]}\n")


