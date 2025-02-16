import base64
import random

import qrcode
from PIL import Image, ImageDraw, ImageFont

def create_qr_label_right(data, label_text, footer_text, height=70, padding = 10, spine_gap = 40):
    # Generate QR code
    qr = qrcode.QRCode(box_size=1, border=0)  # Small border
    qr.add_data(f"https://assett.ag/a/{data}")
    qr.make(fit=True)

    # Create QR code image
    qr_img: Image = qr.make_image(fill="black", back_color="white").convert("RGB")

    # Resize QR code to 70x70px
    qr_size = (height // qr_img.size[1]) * qr_img.size[1]
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)

    # Load tiny bitmap font
    tiny_font = ImageFont.load_default()
    font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf", (height - 5) // 3)
    footer_font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf", (height - 5) // 3)

    font_height = 0
    text_height = 0
    text_width = 0
    # Calculate text size
    for l in label_text.splitlines():
        x,y,font_width,font_height = font.getbbox(l)
        text_width = max(text_width, font_width)
        text_height += font_height

    x, y, footer_width, footer_height = footer_font.getbbox(footer_text)
    text_width = max(text_width, footer_width)

    # Define final image size (QR code width + text width)
    final_width = qr_size * 2 + padding * 4 + text_width + spine_gap
    img = Image.new("RGBA", (final_width, height), "white")
    draw = ImageDraw.Draw(img)

    # Paste QR code on the left
    img.paste(qr_img, (padding, (height - qr_size) // 2))
    img.paste(qr_img, (final_width - padding - qr_size , (height - qr_size) // 2))

    # Draw label text to the right of the QR code
    text_x = qr_size + padding * 2 + spine_gap
    text_y = 0 # (height - text_height) // 2  # Center vertically
    draw.text((text_x, text_y), label_text, font=font, fill="black")
    draw.text((text_x, height - font_height), footer_text, font=footer_font, fill="black")

    edge = qr_size + padding + (spine_gap // 2)
    # Draw a line to show where the edge of the case should be
    draw.line((edge, 0, edge , height), fill="black", width=1)

    # return img

    px_data = img.getdata()

    new_data = []
    for item in px_data:
        # If pixel is white (R=255, G=255, B=255)
        if item[:3] == (255, 255, 255):
            new_data.append((255, 255, 255, 0))  # Make it transparent
        else:
            new_data.append(item)

    img.putdata(new_data)

    return img

# Example usage
rand_64bit = random.getrandbits(64)

# Base64 URL-safe encode and strip padding
base64_encoded = base64.urlsafe_b64encode(rand_64bit.to_bytes(8, 'big')).decode().rstrip('=')

data = base64_encoded
label_text = "Rise of the Planet of the Apes"

if len(label_text) > 20:
    s = label_text.index(" ", len(label_text) // 2)
    label_text = label_text[:s] + "\n" + label_text[s+1:]

qr_label_img = create_qr_label_right(data, label_text, footer_text= base64_encoded)
qr_label_img.show()
qr_label_img.save("qr_label_right.png")