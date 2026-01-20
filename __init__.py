from .nodes import VPypeProcessor, VPypeGCodeGenerator

__version__ = "1.0.0"
__author__ = "Samuele"
__description__ = "ComfyUI nodes for processing SVG and generating G-code using vpype"

NODE_CLASS_MAPPINGS = {
    "VPypeProcessor": VPypeProcessor,
    "VPypeGCodeGenerator": VPypeGCodeGenerator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VPypeProcessor": "VPype SVG Processor",
    "VPypeGCodeGenerator": "VPype G-Code Generator"
}


__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
