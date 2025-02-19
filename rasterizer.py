import sys
import png
import packbits

CHUNK_SIZE = 16
ZERO_CHUNK = bytearray(b"\x00" * CHUNK_SIZE)
RASTER_COMMAND = b"\x47"
ZERO_COMMAND = b"\x5A"


def rasterize(encoded_image_data):
    for i in range(0, len(encoded_image_data), CHUNK_SIZE):
        buffer = bytearray()
        chunk = encoded_image_data[i:i + CHUNK_SIZE]

        if chunk == ZERO_CHUNK:
            buffer += ZERO_COMMAND
        else:
            packed_chunk = packbits.encode(chunk)

            buffer += RASTER_COMMAND
            buffer += len(packed_chunk).to_bytes(2, "little")
            buffer += packbits.encode(chunk)

        yield buffer


def encode_png(image_path, target_height):
    """
    Convert the PNG to a raster for printing

    :param image_path: Path to the PNG file to be printed
    :param target_height: Height we expect the image to be for the given tape size
    """

    margin = (128 - target_height) // 2

    width, height, rows, info = png.Reader(filename=image_path).asRGBA()

    if height != target_height:
        sys.exit(f"Image height is {height} pixels, {target_height} required for the current media width")

    # get all the alpha channel values, rotate 90 degrees and flip horizontally
    data = [row[3::4] for row in rows]
    data = list(zip(*data))

    buffer = bytearray()

    # We need to bit stuff the image to get things to align as for < 24mm tapes, the image will not be a multiple of
    # 8, and we also need to add a left and right margins which are thankfully symmetric
    byte = 0
    bits = 0
    for line in data:
        # Push in left margin bits
        for _ in range(0, margin):
            bits += 1

            if bits == 8:
                buffer.append(byte)
                bits = 0
                byte = 0

        # Push in the image bits for this line of the image
        for v in line:
            if v > 0:
                byte |= (1 << (7 - bits))
            bits += 1

            if bits == 8:
                buffer.append(byte)
                bits = 0
                byte = 0

        # Push in the right margin bits
        for _ in range(0, margin):
            bits += 1

            if bits == 8:
                buffer.append(byte)
                bits = 0
                byte = 0

    return buffer
