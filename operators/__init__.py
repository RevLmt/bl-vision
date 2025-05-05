from .bbox_tracker import register as register_bbox_tracker, unregister as unregister_bbox_tracker


def register():
    register_bbox_tracker()

def unregister():
    unregister_bbox_tracker()