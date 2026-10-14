import os

from PIL import Image

# 3:4 ratio, target size 1200x1600
target_width = 1200
target_height = 1600

# Create the canvas
canvas = Image.new("RGB", (target_width, target_height), (255, 255, 255))

# Top half: AI promo image
top_img_path = "generated-images/A_modern__sleak_promotional_ba_2026-04-08T07-30-09.png"
if not os.path.exists(top_img_path):
    # Try the other one
    top_img_path = "generated-images/A_friendly_cartoon_style_docto_2026-04-08T07-34-43.png"

top_img = Image.open(top_img_path)
# Scale to canvas width, keep aspect ratio, place in the top half
top_aspect = top_img.width / top_img.height
new_top_height = int(target_width / top_aspect)
top_img_resized = top_img.resize((target_width, new_top_height), Image.Resampling.LANCZOS)

# Bottom half: LightClaw screenshot
bottom_img_path = "docs/lightclaw-dashboard.png"
bottom_img = Image.open(bottom_img_path)
# Scale to canvas width, keep aspect ratio
bottom_aspect = bottom_img.width / bottom_img.height
new_bottom_height = int(target_width / bottom_aspect)
bottom_img_resized = bottom_img.resize((target_width, new_bottom_height), Image.Resampling.LANCZOS)

# Compute positions: top image flushed to the top, bottom image flushed to the bottom, gap or crop in between
available_height = target_height
if new_top_height + new_bottom_height <= target_height:
    # Both images fit: stack them vertically with a gap in between
    canvas.paste(top_img_resized, (0, 0))
    canvas.paste(bottom_img_resized, (0, target_height - new_bottom_height))
else:
    # They do not fit: crop proportionally
    top_height_final = int(target_height * 0.5)  # Top half takes up 50%
    bottom_height_final = target_height - top_height_final

    top_img_final = top_img_resized.crop((0, 0, target_width, top_height_final))
    bottom_img_final = bottom_img_resized.crop((0, 0, target_width, bottom_height_final))

    canvas.paste(top_img_final, (0, 0))
    canvas.paste(bottom_img_final, (0, top_height_final))

# Save
output_path = "generated-images/promo-3x4-composite.png"
canvas.save(output_path, "PNG", quality=95)
print(f"✅ Image generated: {output_path}")
print(f"Size: {canvas.width}x{canvas.height} (3:4)")
