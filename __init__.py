from .nodes import VPypeProcessor, VPypeGCodeGenerator
from .vpype_extended_node import VPypeExtendedProcessor

__version__ = "1.0.0"
__author__ = "Samuele"
__description__ = "ComfyUI nodes for processing SVG and generating G-code using vpype"

NODE_CLASS_MAPPINGS = {
    "VPypeProcessor": VPypeProcessor,
    "VPypeGCodeGenerator": VPypeGCodeGenerator,
    "VPypeExtendedProcessor": VPypeExtendedProcessor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VPypeProcessor": "VPype SVG Processor",
    "VPypeGCodeGenerator": "VPype G-Code Generator",
    "VPypeExtendedProcessor": "VPype Extended SVG Processor"
}


__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
