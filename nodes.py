import os
import subprocess
import tempfile
import shutil
import sys

class VPypeProcessor:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "svg_input": ("STRING", {"multiline": True, "forceInput": True, "dynamicPrompts": False}),
                "merge_tolerance": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 10.0, "step": 0.01, "display": "number"}),
                "simplify_tolerance": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 10.0, "step": 0.01, "display": "number"}),
                "min_length": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 100.0, "step": 0.1, "display": "number"}),
                "multipass_count": ("INT", {"default": 0, "min": 0, "max": 50, "step": 1, "display": "number"}),
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

    def process_svg(self, svg_input, merge_tolerance, simplify_tolerance, min_length, multipass_count, rotation, perform_layout, margin, width, height):
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
            ]

            if min_length > 0:
                cmd.extend(["filter", "--min-length", f"{min_length}mm"])

            cmd.append("linesort")

            if multipass_count > 0:
                cmd.extend(["multipass", "--count", str(multipass_count)])

            cmd.extend(["rotate", str(rotation)])
            
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
                "pen_up": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.1, "display": "number"}),
                "pen_down": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 15.0, "step": 0.1, "display": "number"}),
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
F{{vp_speed}}  ; Set Speed  mm/min
G00 Z{{vp_penup}} ; pen up
G92 X0 Y0 ; consider current position as 0,0
\"\"\"

layer_start = "; --- Layer {{layer_index1:d}} ---\\n"

segment_first = \"\""G0 Z{{vp_penup}} ;
G0 X{{x:.3f}} Y{{y:.3f}} ; Initial position
G0 Z{{vp_pendown}} ;
F{{vp_speed}} ; Linear speed
\"\"\"

segment = \"\""G1 X{{x:.3f}} Y{{y:.3f}}\\n\"\"\"

line_end = \"\""G0 Z{{vp_penup}} ; pen up\\n\\n\"\"\"

document_end = \"\""G0 Z{{vp_penup}} ;
G00 X0 Y0; ; return to origin
M2 ; End of program
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

class VPypeRemoveBorder:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "svg_input": ("STRING", {"forceInput": True}),
                "threshold_percentage": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01, "display": "number"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("svg_output",)
    FUNCTION = "remove_border"
    CATEGORY = "VPype"

    def remove_border(self, svg_input, threshold_percentage):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input.svg")
            output_path = os.path.join(temp_dir, "output.svg")
            script_path = os.path.join(temp_dir, "remove_border.py")

            if os.path.isfile(svg_input):
                 shutil.copy(svg_input, input_path)
            else:
                with open(input_path, "w", encoding="utf-8") as f:
                    f.write(svg_input)
            
            # Python script to be executed in the environment
            script_content = """
import sys
try:
    import vpype
    import numpy as np
except ImportError:
    # If vpype is not found as a library, we can't run this script
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]
threshold = float(sys.argv[3])

doc = vpype.read_multilayer_svg(input_file, quantization=1.0)
bounds = doc.bounds()

if bounds:
    min_x, min_y, max_x, max_y = bounds
    doc_width = max_x - min_x
    doc_height = max_y - min_y
    doc_area = doc_width * doc_height
    
    if doc_area > 0:
        for layer in doc.layers.values():
            idxs_to_remove = []
            for i, line in enumerate(layer):
                # line is numpy array of complex
                if len(line) > 0:
                    # Check if closed
                    is_closed = abs(line[0] - line[-1]) < 1e-4
                    if is_closed:
                        # bounding box of the line
                        lx_min = line.real.min()
                        lx_max = line.real.max()
                        ly_min = line.imag.min()
                        ly_max = line.imag.max()
                        
                        l_area = (lx_max - lx_min) * (ly_max - ly_min)
                        
                        if l_area / doc_area >= threshold:
                            idxs_to_remove.append(i)
            
            # Remove indices in reverse order to keep others valid
            for i in sorted(idxs_to_remove, reverse=True):
                del layer[i]

with open(output_file, "w", encoding="utf-8") as f:
    vpype.write_svg(f, doc)
"""
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Build command to run the python script using the current python interpreter
            cmd = [
                sys.executable,
                script_path,
                input_path,
                output_path,
                str(threshold_percentage)
            ]

            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"VPype Remove Border stdout: {result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"VPype Remove Border stderr: {e.stderr}")
                msg = f"Script execution failed: {e.stderr}"
                if "ImportError" in e.stderr or e.returncode == 1:
                     msg += "\nEnsure vpype is installed in the python environment (pip install vpype)."
                raise Exception(msg)

            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    processed_svg = f.read()
                return (processed_svg,)
            else:
                raise Exception("Script did not generate the output file.")


