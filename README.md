# Bar Graph Animation Generator

This Python script creates a series of animated bar graphs where each animation adds one more datapoint to the graph.

## Features

- **Animated Bar Growth**: Each bar animates upwards, composed of colored blocks
- **Stacked Blocks**: Each value in the data becomes a colored block with its text label
- **Labels and Images**: Each bar has a label and an optional image below it
- **Multiple Output Formats**: Generates both static frames and animated GIFs

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script:

```bash
python bargraph_animation.py
```

The script will create:
- Static frame images: `animation_frame_1.png`, `animation_frame_2.png`, `animation_frame_3.png`
- Animated GIFs: `animation_1.gif`, `animation_2.gif`, `animation_3.gif`

All files are saved in the `animations/` folder.

## Data Structure

Each datapoint has the following structure:

```python
{
    'label': 'Product Name',      # Text label below the bar
    'image_path': 'path/to/img',  # Optional image path
    'values': ['x', 'y', 'z']      # List of strings for stacked blocks
}
```

## Customization

Edit the `example_data` list in `bargraph_animation.py` to customize:
- Number of animations
- Bar labels
- Values for each bar
- Image paths (set to `None` for placeholder)

You can also modify the `COLORS` list to change the color palette for the blocks.

"# OmniDocs" 
