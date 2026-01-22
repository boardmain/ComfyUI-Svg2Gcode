import os
import subprocess
import tempfile
import shutil

class VPypeExtendedProcessor:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "svg_input": ("STRING", {"multiline": True, "forceInput": True, "dynamicPrompts": False}),
                
                # Pre-processing
                "linemerge_enable": ("BOOLEAN", {"default": True}),
                "linemerge_tolerance": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 10.0, "step": 0.01, "display": "number"}),
                
                "linesimplify_enable": ("BOOLEAN", {"default": True}),
                "linesimplify_tolerance": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 10.0, "step": 0.01, "display": "number"}),
                
                "reloop_enable": ("BOOLEAN", {"default": False}),
                "reloop_tolerance": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 10.0, "step": 0.01, "display": "number"}),
                
                # Filters / Effects
                "squiggles_enable": ("BOOLEAN", {"default": False}),
                "squiggles_amplitude": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 50.0, "step": 0.1}),
                "squiggles_period": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 100.0, "step": 0.1}),
                
                "filter_min_length": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 100.0, "step": 0.1, "display": "number"}),

                # Occult (Plugin)
                "occult_enable": ("BOOLEAN", {"default": False}),
                "occult_ignore_layers": ("BOOLEAN", {"default": False}),
                "occult_cross_layers": ("BOOLEAN", {"default": False}),
                "occult_keep_occulted": ("BOOLEAN", {"default": False}),
                
                # Optimization
                "linesort_enable": ("BOOLEAN", {"default": True}),
                "linesort_two_opt": ("BOOLEAN", {"default": False}),
                
                # Multipass
                "multipass_count": ("INT", {"default": 1, "min": 1, "max": 50, "step": 1, "display": "number"}),
                
                # Transforms
                "rotate_angle": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 1.0, "display": "number"}),
                "skew_x": ("FLOAT", {"default": 0.0, "min": -89.9, "max": 89.9, "step": 1.0}),
                "skew_y": ("FLOAT", {"default": 0.0, "min": -89.9, "max": 89.9, "step": 1.0}),
                "scale_x": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 100.0, "step": 0.01}),
                "scale_y": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 100.0, "step": 0.01}),
                
                # Layout
                "layout_enable": ("BOOLEAN", {"default": True}),
                "layout_width": ("FLOAT", {"default": 210.0, "min": 10.0, "max": 5000.0, "step": 1.0, "display": "number"}), # A4 width
                "layout_height": ("FLOAT", {"default": 297.0, "min": 10.0, "max": 5000.0, "step": 1.0, "display": "number"}), # A4 height
                "layout_margin": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 100.0, "step": 0.1, "display": "number"}),
                "layout_align": (["center", "left", "right"],),
                "layout_valign": (["center", "top", "bottom"],),
                "layout_fit_to_margins": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("svg_output",)
    FUNCTION = "process_svg"
    CATEGORY = "VPype"

    def process_svg(self, svg_input, 
                    linemerge_enable, linemerge_tolerance,
                    linesimplify_enable, linesimplify_tolerance,
                    reloop_enable, reloop_tolerance,
                    squiggles_enable, squiggles_amplitude, squiggles_period,
                    filter_min_length,
                    occult_enable, occult_ignore_layers, occult_cross_layers, occult_keep_occulted,
                    linesort_enable, linesort_two_opt,
                    multipass_count,
                    rotate_angle, skew_x, skew_y, scale_x, scale_y,
                    layout_enable, layout_width, layout_height, layout_margin, layout_align, layout_valign, layout_fit_to_margins):
        
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input.svg")
            output_path = os.path.join(temp_dir, "output.svg")

            # Validate input
            if os.path.isfile(svg_input):
                 shutil.copy(svg_input, input_path)
            else:
                with open(input_path, "w", encoding="utf-8") as f:
                    f.write(svg_input)

            # Build Command
            cmd = ["vpype", "read", "--attr", "stroke", input_path]

            if linemerge_enable:
                cmd.extend(["linemerge", "--tolerance", f"{linemerge_tolerance}mm"])
            
            if linesimplify_enable:
                cmd.extend(["linesimplify", "--tolerance", f"{linesimplify_tolerance}mm"])

            if reloop_enable:
                cmd.extend(["reloop", "--tolerance", f"{reloop_tolerance}mm"])

            if squiggles_enable:
                cmd.extend(["squiggles", "--amplitude", f"{squiggles_amplitude}mm", "--period", f"{squiggles_period}mm"])

            if filter_min_length > 0:
                cmd.extend(["filter", "--min-length", f"{filter_min_length}mm"])

            if occult_enable:
                occult_cmd = ["occult"]
                if occult_ignore_layers:
                    occult_cmd.append("-i")
                if occult_cross_layers:
                    occult_cmd.append("-a")
                if occult_keep_occulted:
                    occult_cmd.append("-k")
                cmd.extend(occult_cmd)

            if linesort_enable:
                sort_cmd = ["linesort"]
                if linesort_two_opt:
                    sort_cmd.append("--two-opt")
                cmd.extend(sort_cmd)

            if multipass_count > 1:
                cmd.extend(["multipass", "--count", str(multipass_count)])

            if rotate_angle != 0:
                cmd.extend(["rotate", str(rotate_angle)])

            if skew_x != 0 or skew_y != 0:
                cmd.extend(["skew", str(skew_x), str(skew_y)])

            if scale_x != 1.0 or scale_y != 1.0:
                if scale_x == scale_y:
                    cmd.extend(["scale", str(scale_x)])
                else:
                    cmd.extend(["scale", str(scale_x), str(scale_y)])

            if layout_enable:
                layout_cmd = ["layout"]
                if layout_fit_to_margins:
                    layout_cmd.extend(["--fit-to-margins", f"{layout_margin}mm"])
                
                layout_cmd.extend(["--align", layout_align])
                layout_cmd.extend(["--valign", layout_valign])
                
                layout_cmd.append(f"{layout_width}mmx{layout_height}mm")
                cmd.extend(layout_cmd)

            cmd.extend(["write", output_path])

            try:
                # Run VPype
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"VPype stdout: {result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"VPype stderr: {e.stderr}")
                msg = f"VPype execution failed.\nCommand: {' '.join(cmd)}\nError: {e.stderr}"
                raise Exception(msg)
            except FileNotFoundError:
                raise Exception("vpype executable not found. Please ensure it is installed and in your PATH.")

            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    processed_svg = f.read()
                return (processed_svg,)
            else:
                raise Exception("VPype did not generate the output file.")
