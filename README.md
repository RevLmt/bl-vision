# BL Vision: Blender Synthetic Dataset Generator

**Generate 2D bounding boxes directly in Blender for object detection datasets.**  
Export in YOLO or COCO format. Automate multi-angle, multi-light dataset creation—no coding required.

---

## Features

- Generate bounding boxes for **objects, collections, and particles**
- Export labels in **YOLO or COCO** format
- Designed for **fast synthetic dataset creation** inside Blender
- Outputs paired images and annotation files ready for training
- Fully supports Blender 4.2+

---

## 🔍 Use Cases

Ideal for:

- Training custom object detection models
- Generating domain-randomized data
- Applications in robotics, retail, and autonomous systems
- Rapid prototyping with synthetic images

---

## 📥 Installation

To install the add-on in Blender:

1. Clone or download this repository as a ZIP file.
2. Open Blender (version 4.2 or higher).
3. Go to **Edit > Preferences**.
    ![Blender Preferences Location](/images/blender-preferences.png)
4. Select the **Add-ons** tab.
5. Click the **downward-facing arrow icon** in the upper right corner.
6. Choose **Install from Disk...** from the dropdown.
    ![Install from disk](/images/Install_from_disk.png)
7. Select the downloaded ZIP file.
8. Enable the checkbox next to the add-on to activate it.

---

## Where to Access

1. Press N in the 3D Viewport.
2. Click on the tab BL Vision.

## How to Use

1. Select a mode: Object, Collection, or Particle Emitter
2. Select items (objects, collections, or particle emitters) you would like to generate annotations for.
3. Assign category ID's either manually or using the "Auto Assign Categories" button.
4. To ignore items blocked/occluded from the active camera view, click Raycast.
5. In Data Output, select a format.
6. Check Bounding Box to open up save path options.
7. Render the Animation (CTRL + F12).
8. View your bounding boxes in the directory you chose.

## 🛠️ Upcoming Features

- Segmentation mask support
- Object-oriented bounding boxes
- Object pose annotation support

---

## 📄 License

This project is licensed under the GPL-3.0 License.
