import qrcode
from PIL import Image, ImageDraw, ImageFont
import uuid

def create_qr_label_right(data, label_text, barcode, height=70):
    # Generate QR code
    qr = qrcode.QRCode(box_size=1, border=0)  # Small border
    qr.add_data("https://assett.ag/data")
    qr.make(fit=True)

    # Create QR code image
    qr_img: Image = qr.make_image(fill="black", back_color="white").convert("RGB")

    # Resize QR code to 70x70px
    qr_size = (height // qr_img.size[1]) * qr_img.size[1]
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)

    # Load tiny bitmap font
    tiny_font = ImageFont.load_default()
    font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf", (height - 10) // 3)
    bc_font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf", (height - 10) // 3)

    text_height = 0
    text_width = 0
    # Calculate text size
    for l in label_text.splitlines():
        x,y,font_width,font_height = font.getbbox(l)
        text_width = max(text_width, font_width)
        text_height += font_height

    # barcode = "1234567890123"
    x, y, bc_width, bc_height = bc_font.getbbox(barcode)
    text_width = max(text_width, bc_width)

    # Define final image size (QR code width + text width)
    padding = 5  # Space between QR code and text
    final_width = qr_size + padding * 3 + text_width
    img = Image.new("RGBA", (final_width, height), "white")
    draw = ImageDraw.Draw(img)

    # Paste QR code on the left
    img.paste(qr_img, (padding, (height - qr_img.size[1]) // 2))
    # img.paste(qr_img, (0, 0))

    # Draw label text to the right of the QR code
    text_x = qr_size + padding * 2
    text_y = 0 # (height - text_height) // 2  # Center vertically
    draw.text((text_x, text_y), label_text, font=font, fill="black")
    draw.text((text_x, height - font_height), barcode, font=bc_font, fill="black")

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
data = str(uuid.uuid4())
label_text = "Some Random Movie Title that is really long"

if len(label_text) > 20:
    s = label_text.index(" ", len(label_text) // 2)
    label_text = label_text[:s] + "\n" + label_text[s+1:]

qr_label_img = create_qr_label_right(data, label_text, barcode = "1234567890123")
qr_label_img.show()
qr_label_img.save("qr_label_right.png")