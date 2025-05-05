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

from .save_panel import register as register_save, unregister as unregister_save
from .panel_bbox import register as register_bbox, unregister as unregister_bbox

def register():


    register_save()
    register_bbox()
    


def unregister():


    unregister_save()
    unregister_bbox()