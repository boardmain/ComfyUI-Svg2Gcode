# ComfyUI VPype Node

This is a custom node for ComfyUI that processes SVG files using `vpype`.

## Features

Applies the following `vpype` pipeline:

- `linemerge` (tolerance configurable)
- `linesimplify` (tolerance configurable)
- `linesort`
- `rotate` (angle configurable)
- `layout` (fit to margins, centered on specified page size)

## Inputs

- **svg_input**: SVG content (string) or file path.
- **merge_tolerance**: Tolerance for `linemerge` (mm).
- **simplify_tolerance**: Tolerance for `linesimplify` (mm).
- **rotation**: Rotation angle (degrees).
- **margin**: Page margin (mm).
- **width**: Page width (mm).
- **height**: Page height (mm).

## Output

- **svg_output**: Processed SVG content as a string.

## Installation

1. Clone this repository into your `ComfyUI/custom_nodes` folder.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
   (Make sure you use the `pip` associated with your ComfyUI python environment).
3. Ensure the `vpype` command is accessible in your system path or environment.
