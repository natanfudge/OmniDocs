import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from PIL import Image
import os
import json
import glob

def load_data_from_json(json_path='data.json'):
    """Load product data from a JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Sort by number of values (ascending)
        data_sorted = sorted(data, key=lambda x: len(x['values']))
        return data_sorted
    except FileNotFoundError:
        print(f"Warning: {json_path} not found. Using default example data.")
        return [
            {
                'label': 'Product B',
                'image_path': 'replit-color.png',
                'values': ['a', 'b']
            },
            {
                'label': 'Product A',
                'image_path': 'cursor-ai.png',
                'values': ['x', 'y', 'a']
            },
            {
                'label': 'Product C',
                'image_path': 'Claude_AI_symbol.svg.png',
                'values': ['m', 'n', 'x', 'b']
            }
        ]

def reorder_values_with_history(data_points):
    """
    Reorder values in each bar so that values from previous bars appear first (at the bottom).
    Values are ordered by when they first appeared.
    """
    seen_values = []  # Track values in order of first appearance
    reordered_data = []

    for data in data_points:
        current_values = data['values']

        # Separate into old values (already seen) and new values
        old_values = []
        new_values = []

        for value in current_values:
            if value in seen_values:
                old_values.append(value)
            else:
                new_values.append(value)
                seen_values.append(value)  # Add to seen list

        # Sort old values by their first appearance order
        old_values_sorted = [v for v in seen_values if v in old_values]

        # Combine: old values first (bottom), then new values (top)
        reordered_values = old_values_sorted + new_values

        reordered_data.append({
            'label': data['label'],
            'image_path': data['image_path'],
            'values': reordered_values
        })

    return reordered_data

# Color palette for the blocks
COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2', 
          '#FFB347', '#87CEEB', '#DDA0DD', '#F0E68C', '#98FB98', '#FF6347', '#40E0D0', '#EE82EE']

def get_value_color_mapping(data_points):
    """
    Create a mapping of unique values to colors.
    All instances of the same value across all bars will have the same color.
    """
    # Collect all unique values
    unique_values = set()
    for data in data_points:
        unique_values.update(data['values'])
    
    # Create mapping
    value_to_color = {}
    for idx, value in enumerate(sorted(unique_values)):
        value_to_color[value] = COLORS[idx % len(COLORS)]
    
    return value_to_color

def create_animated_gif(data_points, animation_num, output_path, partial_mode=False):
    """
    Create an animated GIF showing the bar growing upwards.
    On animation n, all bars x<n are static, only bar n animates.
    Each block has a 1 second delay when completed before the next block starts.

    If partial_mode is True, only shows the currently animating bar.
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    if partial_mode:
        # Only show the currently animating bar
        current_data = [data_points[animation_num - 1]]
        # Adjust animation_num for the partial view (it's always the first bar)
        display_animation_num = 1
    else:
        # Show all bars up to current
        current_data = data_points[:animation_num]
        display_animation_num = animation_num
    max_height = max(len(dp['values']) for dp in data_points) + 2
    
    # Get value-to-color mapping
    value_color_map = get_value_color_mapping(data_points)
    
    ax.set_xlim(-1, len(data_points) * 3.3 - 1)
    ax.set_ylim(-2.5, max_height)  # Extra space for label and image below
    ax.set_title('Quality', fontsize=16, fontweight='bold')
    
    # Remove Y-axis numbering and horizontal grid lines
    ax.set_yticks([])
    ax.grid(False)
    
    # Remove all spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    # Remove x-axis labels
    ax.set_xticks([])
    
    # Animation parameters
    FRAMES_PER_BLOCK_NEW = 15  # Frames to animate one new block
    DELAY_FRAMES_NEW = 20  # 1 second delay for new blocks at 20fps = 20 frames
    FRAMES_PER_BLOCK_OLD = 5   # Frames to animate one old block (much faster)
    DELAY_FRAMES_OLD = 5       # Shorter delay for old blocks
    FPS = 20
    
    # Identify which values in each bar are "old" (appeared in previous bars)
    def get_old_values_map(data_points, animation_num):
        """Returns a dict mapping bar index to set of old values for that bar."""
        seen_values = set()
        old_values_map = {}

        for i in range(animation_num):
            old_values = set()
            for value in data_points[i]['values']:
                if value in seen_values:
                    old_values.add(value)
                else:
                    seen_values.add(value)
            old_values_map[i] = old_values

        return old_values_map

    # For old values tracking, use original data_points and animation_num
    old_values_map = get_old_values_map(data_points, animation_num)

    # Calculate total frames needed for the newest bar
    if animation_num > 0:
        newest_bar_values = data_points[animation_num - 1]['values']
        newest_bar_old_values = old_values_map.get(animation_num - 1, set())

        # Calculate frames based on old vs new values
        total_frames = 0
        for value in newest_bar_values:
            if value in newest_bar_old_values:
                total_frames += FRAMES_PER_BLOCK_OLD + DELAY_FRAMES_OLD
            else:
                total_frames += FRAMES_PER_BLOCK_NEW + DELAY_FRAMES_NEW
    else:
        total_frames = 60
    
    # Store animation elements
    rects = []
    texts = []
    images = []
    
    def init():
        return []
    
    def calculate_animated_height(frame, bar_idx, bar_values, is_newest_bar):
        """
        Calculate the animated height for a bar.
        For the newest bar, includes delays between blocks.
        Old values animate faster with shorter delays than new values.
        """
        if not is_newest_bar:
            return len(bar_values)  # Static complete bar

        # For the newest bar, calculate with delays
        old_values_for_bar = old_values_map.get(bar_idx, set())
        current_frame = frame
        animated_height = 0
        cumulative_frame = 0

        for block_idx in range(len(bar_values)):
            value = bar_values[block_idx]
            is_old = value in old_values_for_bar

            # Use different timing for old vs new values
            frames_for_block = FRAMES_PER_BLOCK_OLD if is_old else FRAMES_PER_BLOCK_NEW
            delay_for_block = DELAY_FRAMES_OLD if is_old else DELAY_FRAMES_NEW

            block_start_frame = cumulative_frame
            block_end_frame = block_start_frame + frames_for_block
            cumulative_frame += frames_for_block + delay_for_block

            if current_frame >= block_end_frame:
                # Block is complete (including during delay period)
                animated_height += 1.0
            elif current_frame >= block_start_frame:
                # Block is currently animating
                block_progress = (current_frame - block_start_frame) / frames_for_block
                animated_height += block_progress
                break
            else:
                # Block hasn't started yet - all previous blocks are complete
                break

        return animated_height
    
    def animate(frame):
        # Clear previous frame elements
        for rect in rects:
            rect.remove()
        rects.clear()
        for text in texts:
            text.remove()
        texts.clear()
        for img in images:
            img.remove()
        images.clear()
        
        for i, data in enumerate(current_data):
            x_pos = i * 3.3  # Triple spacing between bars (with 10% extra)
            bar_values = data['values']
            # In partial mode, the only bar shown is always the newest
            if partial_mode:
                is_newest_bar = True
                # Use the original index for old_values_map lookup
                original_bar_idx = animation_num - 1
            else:
                is_newest_bar = (i == animation_num - 1)
                original_bar_idx = i

            # Calculate animated height using original bar index
            animated_height = calculate_animated_height(frame, original_bar_idx, bar_values, is_newest_bar)
            
            # Create stacked blocks up to animated_height
            y_bottom = 0
            block_index = 0
            while y_bottom < animated_height and block_index < len(bar_values):
                block_height = min(1.0, animated_height - y_bottom)
                if block_height > 0.01:  # Only draw if visible
                    value = data['values'][block_index]
                    color = value_color_map.get(value, COLORS[0])
                    
                    rect = patches.Rectangle(
                        (x_pos - 0.3, y_bottom), 
                        0.6, 
                        block_height, 
                        linewidth=1.5,
                        edgecolor='black',
                        facecolor=color,
                        alpha=0.8
                    )
                    ax.add_patch(rect)
                    rects.append(rect)
                    
                    # Add text if block is mostly visible
                    if block_height > 0.5:
                        # Replace spaces with newlines for multi-word values
                        display_text = value.replace(' ', '\n')
                        text = ax.text(
                            x_pos + 0.4,
                            y_bottom + block_height/2,
                            display_text,
                            fontsize=9,
                            verticalalignment='center',
                            fontweight='bold'
                        )
                        texts.append(text)
                
                y_bottom += 1
                block_index += 1
            
            # Add label text (above the image)
            label_text = ax.text(
                x_pos, 
                -0.8, 
                data['label'], 
                ha='center',
                fontsize=12,
                fontweight='bold'
            )
            texts.append(label_text)
            
            # Load and display image below the label
            if data['image_path'] and os.path.exists(data['image_path']):
                try:
                    img = Image.open(data['image_path'])
                    # Get image dimensions
                    img_width, img_height = img.size
                    img_aspect = img_width / img_height
                    
                    # Available space for image (larger icons)
                    available_width = 1.2  # Increased from 0.5
                    available_height = 1.2  # Increased from 0.5
                    available_aspect = available_width / available_height
                    
                    # Calculate display dimensions maintaining aspect ratio
                    if img_aspect > available_aspect:
                        # Image is wider - fit to width
                        display_width = available_width
                        display_height = available_width / img_aspect
                    else:
                        # Image is taller - fit to height
                        display_height = available_height
                        display_width = available_height * img_aspect
                    
                    # Center the image (moved lower to avoid label overlap)
                    x_center = x_pos
                    y_center = -1.5  # Moved down from -1.25
                    x_left = x_center - display_width / 2
                    x_right = x_center + display_width / 2
                    y_bottom = y_center - display_height / 2
                    y_top = y_center + display_height / 2
                    
                    im = ax.imshow(img, extent=[x_left, x_right, y_bottom, y_top], zorder=3)
                    images.append(im)
                except Exception as e:
                    print(f"Could not load image {data['image_path']}: {e}")
                    # Fallback to placeholder
                    img_rect = patches.Rectangle(
                        (x_pos - 0.25, -1.5),
                        0.5,
                        0.5,
                        linewidth=1,
                        edgecolor='gray',
                        facecolor='lightgray',
                        alpha=0.5
                    )
                    ax.add_patch(img_rect)
                    rects.append(img_rect)
            else:
                # Draw a placeholder rectangle for the image
                img_rect = patches.Rectangle(
                    (x_pos - 0.25, -1.5),
                    0.5,
                    0.5,
                    linewidth=1,
                    edgecolor='gray',
                    facecolor='lightgray',
                    alpha=0.5
                )
                ax.add_patch(img_rect)
                rects.append(img_rect)
        
        return rects + texts + images
    
    # Create animation
    anim = FuncAnimation(
        fig, 
        animate, 
        init_func=init,
        frames=total_frames,
        interval=50,  # 50ms per frame (20fps)
        blit=False,
        repeat=True
    )
    
    # Save as GIF
    anim.save(
        output_path,
        writer='pillow',
        fps=FPS,
        dpi=100
    )
    plt.close()

def process_data_file(json_path):
    """Process a single data file and create animations."""
    # Extract suffix from filename (e.g., data_foo.json -> foo, data.json -> "")
    base_name = os.path.basename(json_path)
    if base_name == 'data.json':
        suffix = ''
        output_dir = 'animations'
    else:
        # Extract suffix after 'data_'
        suffix = base_name.replace('data_', '').replace('.json', '')
        output_dir = f'animations_{suffix}'

    print(f"\nProcessing {json_path}...")

    # Load data from JSON file
    data = load_data_from_json(json_path)
    print(f"Loaded {len(data)} products from {json_path}.")

    # Reorder values so intersecting values appear at the bottom
    data = reorder_values_with_history(data)

    # Create output directories
    full_dir = os.path.join(output_dir, 'full')
    partial_dir = os.path.join(output_dir, 'partial')
    os.makedirs(full_dir, exist_ok=True)
    os.makedirs(partial_dir, exist_ok=True)

    # Create animated GIFs for each animation
    for i in range(1, len(data) + 1):
        print(f"  Creating animated GIF {i} (full and partial)...")

        # Create full animation (all bars up to current)
        full_path = os.path.join(full_dir, f'animation_{i}.gif')
        create_animated_gif(data, i, full_path, partial_mode=False)

        # Create partial animation (only current bar)
        partial_path = os.path.join(partial_dir, f'animation_{i}.gif')
        create_animated_gif(data, i, partial_path, partial_mode=True)

    print(f"Completed {json_path}!")
    print(f"  Output directory: {output_dir}/")
    print(f"    - full/: Full animations with all bars")
    print(f"    - partial/: Individual bar animations")

def main():
    print("Creating bar graph animations...\n")

    # Find all data files matching pattern data*.json
    data_files = glob.glob('data*.json')

    if not data_files:
        print("No data*.json files found in current directory.")
        return

    print(f"Found {len(data_files)} data file(s): {', '.join(data_files)}\n")

    # Process each data file
    for data_file in sorted(data_files):
        process_data_file(data_file)

    print("\n" + "="*60)
    print("All animations created successfully!")
    print("="*60)

if __name__ == "__main__":
    main()

