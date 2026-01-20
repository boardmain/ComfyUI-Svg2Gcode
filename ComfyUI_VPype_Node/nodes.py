import os
import subprocess
import tempfile
import shutil

class VPypeProcessor:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "svg_input": ("STRING", {"multiline": True, "forceInput": True, "dynamicPrompts": False}),
                "merge_tolerance": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 10.0, "step": 0.01, "display": "number"}),
                "simplify_tolerance": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 10.0, "step": 0.01, "display": "number"}),
                "rotation": ("FLOAT", {"default": 90.0, "min": -360.0, "max": 360.0, "step": 1.0, "display": "number"}),
                "margin": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 100.0, "step": 0.1, "display": "number"}),
                "width": ("FLOAT", {"default": 210.0, "min": 10.0, "max": 5000.0, "step": 1.0, "display": "number"}), # Default A4 approx
                "height": ("FLOAT", {"default": 297.0, "min": 10.0, "max": 5000.0, "step": 1.0, "display": "number"}), # Default A4 approx
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("svg_output",)
    FUNCTION = "process_svg"
    CATEGORY = "VPype"

    def process_svg(self, svg_input, merge_tolerance, simplify_tolerance, rotation, margin, width, height):
        # Create a temporary directory to work in
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input.svg")
            output_path = os.path.join(temp_dir, "output.svg")

            # Check if svg_input is a file path or content
            if os.path.isfile(svg_input):
                 shutil.copy(svg_input, input_path)
            else:
                # Assume it's SVG content string
                with open(input_path, "w", encoding="utf-8") as f:
                    f.write(svg_input)

            # Construct the vpype command
            # Note: vpype needs to be installed in the environment where ComfyUI is running
            cmd = [
                "vpype",
                "read", input_path,
                "linemerge", "--tolerance", f"{merge_tolerance}mm",
                "linesimplify", "--tolerance", f"{simplify_tolerance}mm",
                "linesort",
                "rotate", str(rotation),
                "layout", "--fit-to-margins", f"{margin}mm", 
                          "--align", "center", 
                          "--valign", "center", 
                          f"{width}mmx{height}mm",
                "write", output_path
            ]

            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"VPype stdout: {result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"VPype stderr: {e.stderr}")
                raise Exception(f"VPype execution failed: {e.stderr}")

            # Read the processed SVG
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    processed_svg = f.read()
                return (processed_svg,)
            else:
                raise Exception("VPype did not generate the output file.")
