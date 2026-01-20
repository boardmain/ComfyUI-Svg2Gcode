from .nodes import VPypeProcessor

NODE_CLASS_MAPPINGS = {
    "VPypeProcessor": VPypeProcessor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VPypeProcessor": "VPype SVG Processor"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
