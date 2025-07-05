# BL Vision: Blender Synthetic Dataset Generator

**Generate 2D bounding boxes directly in Blender for object detection datasets.**  
Export in YOLO or COCO format. Automate multi-angle, multi-light dataset creation—no coding required.

To get free starter Blender files along with the add-on, check out my website: [RRX Engineering GumRoad](https://rrxengineering.gumroad.com/l/bl-vision)

For a walkthrough check out the YouTube video on it: [BL-Vision Walkthrough](https://youtu.be/RpkObzZebEw?si=HOy2GaxOPvOS5cUb)

For an article covering the motivation behind this add-on as well as some background: 
[Towards an Accessible Way of Creating Synthetic Images for Vision Models](https://medium.com/ai-advances/towards-an-accessible-way-of-creating-synthetic-images-for-vision-models-b7117cf2a155?sk=94505de6b19fa226babc5d4458da6a7f)

[**Documentation**](https://github.com/RevLmt/bl-vision/wiki) is on the GitHub Wiki of this Repo.

**Important** The easiest, most stable install comes by downloading the latest release!

---

## Features

- Generate bounding boxes for **objects, collections, and particles**
- Export labels in **YOLO or COCO** format
- Designed for **fast synthetic dataset creation** inside Blender
- Outputs paired images and annotation files ready for training
- Fully supports Blender 4.2+
- Updates via the Blender GUI. Only need to install once.

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

1. **Download the latest release as a ZIP file.**
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

## Updates
Comes with an updater inside of the Blender GUI. Any new releases will be available there. No need to go to GitHub to download the latest release. 

To update:
1. Go to Preferences
2. Go to Add-Ons
3. Expand the tab for bl-vision
4. Click check for updates

## 🛠️ Upcoming Features

- Segmentation mask support
- Object-oriented bounding boxes
- Object pose annotation support

## Contribution
Contribuiting guidelines coming soon!

---

## 📄 License

This project is licensed under the GPL-3.0 License.
