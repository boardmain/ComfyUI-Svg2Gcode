from .nodes import VPypeProcessor, VPypeGCodeGenerator

NODE_CLASS_MAPPINGS = {
    "VPypeProcessor": VPypeProcessor,
    "VPypeGCodeGenerator": VPypeGCodeGenerator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VPypeProcessor": "VPype SVG Processor",
    "VPypeGCodeGenerator": "VPype G-Code Generator"
}


__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
