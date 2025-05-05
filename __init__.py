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

bl_info = {
    "name": "bl-vision",
    "blender": (4, 2, 0),
    "category": "Object",
    "author": "Ryan Revilla",
    "version": (1, 0, 0),
    "description": "A UI panel for parenting objects with custom properties",
}

import bpy
from .ui import panel_bbox, save_panel
from .operators import bbox_tracker

def register():
    panel_bbox.register()
    bbox_tracker.register()

    save_panel.register()


def unregister():

    panel_bbox.unregister()
    bbox_tracker.unregister()

    save_panel.unregister()


if __name__ == "__main__":
    register()


