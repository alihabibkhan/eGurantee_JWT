# from PIL import Image, ImageDraw
#
# # Load the image
# image = Image.open("static/images/khushali-logo.png").convert("RGBA")
#
# # Create circular mask
# width, height = image.size
# mask = Image.new('L', (width, height), 0)
# draw = ImageDraw.Draw(mask)
# draw.ellipse((0, 0, width, height), fill=255)
#
# # Apply mask to image
# result = Image.new("RGBA", (width, height))
# result.paste(image, (0, 0), mask)
#
# # Save the result with transparent background
# result.save("khushali-logo-rounded-transparent.png")

from PIL import Image

# Load the image and ensure it has an alpha channel (for transparency)
image = Image.open("static/images/khushali-logo.png").convert("RGBA")

# Get the image data
data = image.getdata()

# Replace white background with transparency
new_data = []
for item in data:
    # Change all white (or near-white) pixels to transparent
    if item[0] > 240 and item[1] > 240 and item[2] > 240:
        new_data.append((255, 255, 255, 0))  # Transparent
    else:
        new_data.append(item)

# Update image data
image.putdata(new_data)

# Save result
image.save("khushali-logo-transparent.png")