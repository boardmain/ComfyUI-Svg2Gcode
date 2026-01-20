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
                "perform_layout": ("BOOLEAN", {"default": True}),
                "margin": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 100.0, "step": 0.1, "display": "number"}),
                "width": ("FLOAT", {"default": 210.0, "min": 10.0, "max": 5000.0, "step": 1.0, "display": "number"}), # Default A4 approx
                "height": ("FLOAT", {"default": 297.0, "min": 10.0, "max": 5000.0, "step": 1.0, "display": "number"}), # Default A4 approx
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("svg_output",)
    FUNCTION = "process_svg"
    CATEGORY = "VPype"

    def process_svg(self, svg_input, merge_tolerance, simplify_tolerance, rotation, perform_layout, margin, width, height):
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
            ]
            
            if perform_layout:
                cmd.extend([
                    "layout", "--fit-to-margins", f"{margin}mm", 
                              "--align", "center", 
                              "--valign", "center", 
                              f"{width}mmx{height}mm"
                ])
                
            cmd.extend(["write", output_path])

            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"VPype stdout: {result.stdout}")
                print(f"VPype stderr: {result.stderr}")
            except subprocess.CalledProcessError as e:
                print(f"VPype stderr: {e.stderr}")
                raise Exception(f"VPype execution failed: {e.stderr}")
            except FileNotFoundError:
                raise Exception("vpype executable not found. Please ensure it is installed and in your PATH.")

            # Read the processed SVG
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    processed_svg = f.read()
                return (processed_svg,)
            else:
                msg = f"VPype did not generate the output file.\nReturn Code: {result.returncode}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"
                raise Exception(msg)

class VPypeGCodeGenerator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "svg_input": ("STRING", {"forceInput": True}),
                "pen_up": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0, "step": 0.1, "display": "number"}),
                "pen_down": ("FLOAT", {"default": 0.0, "min": -10.0, "max": 10.0, "step": 0.1, "display": "number"}),
                "speed": ("FLOAT", {"default": 1000.0, "min": 1.0, "max": 10000.0, "step": 10.0, "display": "number"}),
                "invert_y": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("gcode_output",)
    FUNCTION = "generate_gcode"
    CATEGORY = "VPype"

    def generate_gcode(self, svg_input, pen_up, pen_down, speed, invert_y):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input.svg")
            output_path = os.path.join(temp_dir, "output.gcode")
            config_path = os.path.join(temp_dir, "config.toml")

            # Save input SVG
            if os.path.isfile(svg_input):
                 shutil.copy(svg_input, input_path)
            else:
                with open(input_path, "w", encoding="utf-8") as f:
                    f.write(svg_input)

            # Create configuration file
            # Note: Double curly braces {{ }} are used to escape braces for Python f-strings
            config_content = f"""
[gwrite.default]
unit = "mm"
invert_y = {str(invert_y).lower()}
default_values = {{ vp_penup = "{pen_up}", vp_pendown = "{pen_down}", vp_speed = {speed} }}

document_start = \"\""; G-code generated by vpype-gcode
G21 ; Set Units to Millimeters
G17 ; Set Plane Selection to XY
G90 ; Set Absolute Positioning
F{{vp_speed:d}}  ; Set Speed  mm/min
G00 Z{{vp_penup}} ; pen up
G92 X0 Y0 ; consider current position as 0,0
\"\"\"

layer_start = "; --- Layer {{layer_index1:d}} ---\\n"

segment_first = \"\""G0 Z{{vp_penup}} ;
G0 X{{x:.3f}} Y{{y:.3f}} ; Initial position
G0 Z{{vp_pendown}} ;
F{{vp_speed:d}} ; Linear speed
\"\"\"

segment = \"\""G1 X{{x:.3f}} Y{{y:.3f}}\\n\"\"\"

line_end = \"\""G0 Z{{vp_penup}} ; pen up\\n\\n\"\"\"

document_end = \"\""G0 Z{{vp_penup}} ;
G00 X0 Y
\"\"\"
"""
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)

            cmd = [
                "vpype",
                "-c", config_path,
                "read", input_path,
                "gwrite", "-p", "default",
                output_path
            ]

            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"VPype GCode stdout: {result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"VPype GCode stderr: {e.stderr}")
                raise Exception(f"VPype GCode execution failed: {e.stderr}")

            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    gcode_content = f.read()
                return (gcode_content,)
            else:
                raise Exception("VPype did not generate the GCode file.")

