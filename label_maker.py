import contextlib
import sys
from enum import IntEnum, IntFlag

import bluetooth
from bluetooth import BluetoothError

import app_args
from config import set_default_bt, get_default_bt
from label_rasterizer import encode_png, rasterize

STATUS_OFFSET_ERROR_INFORMATION_1 = 8
STATUS_OFFSET_ERROR_INFORMATION_2 = 9
STATUS_OFFSET_MEDIA_WIDTH = 10
STATUS_OFFSET_MEDIA_TYPE = 11
STATUS_OFFSET_MODE = 15
STATUS_OFFSET_MEDIA_LENGTH = 17
STATUS_OFFSET_STATUS_TYPE = 18
STATUS_OFFSET_PHASE_TYPE = 19
STATUS_OFFSET_PHASE_NUMBER = 20
STATUS_OFFSET_NOTIFICATION_NUMBER = 22
STATUS_OFFSET_TAPE_COLOR_INFORMATION = 24
STATUS_OFFSET_TEXT_COLOR_INFORMATION = 25
STATUS_OFFSET_HARDWARE_SETTINGS = 26

# Map the size of tape to the number of dots on the print area
TZE_DOTS = {
    3: 24,  # Actually 3.5mm, not sure how this is reported if its 3 or 4
    6: 32,
    9: 50,
    12: 70,
    18: 112,
    24: 128
}

# Global for the media width so we can make sure we rasterize/ print to the right size
detected_media_width = -1


class ErrorInformation1(IntFlag):
    NO_MEDIA = 0x01
    CUTTER_JAM = 0x04
    WEAK_BATTERIES = 0x08
    HIGH_VOLTAGE_ADAPTER = 0x40


class ErrorInformation2(IntFlag):
    WRONG_MEDIA = 0x01
    COVER_OPEN = 0x10
    OVERHEATING = 0x20


class MediaType(IntEnum):
    NO_MEDIA = 0x00
    LAMINATED_TAPE = 0x01
    NON_LAMINATED_TAPE = 0x03
    HEAT_SHRINK_TUBE = 0x11
    INCOMPATIBLE_TAPE = 0xFF


class Mode(IntFlag):
    AUTO_CUT = 0x40
    MIRROR_PRINTING = 0x80


class StatusType(IntEnum):
    REPLY_TO_STATUS_REQUEST = 0x00
    PRINTING_COMPLETED = 0x01
    ERROR_OCCURRED = 0x02
    TURNED_OFF = 0x04
    NOTIFICATION = 0x05
    PHASE_CHANGE = 0x06


class PhaseType(IntEnum):
    EDITING_STATE = 0x00
    PRINTING_STATE = 0x01


class PhaseNumberEditingState(IntEnum):
    EDITING_STATE = 0x0000
    FEED = 0x0001


class PhaseNumberPrintingState(IntEnum):
    PRINTING = 0x0000
    COVER_OPEN_WHILE_RECEIVING = 0x0014


class NotificationNumber(IntEnum):
    NOT_AVAILABLE = 0x00
    COVER_OPEN = 0x01
    COVER_CLOSED = 0x02


class TapeColor(IntEnum):
    WHITE = 0x01
    OTHER = 0x02
    CLEAR = 0x03
    RED = 0x04
    BLUE = 0x05
    YELLOW = 0x06
    GREEN = 0x07
    BLACK = 0x08
    CLEAR_WHITE_TEXT = 0x09
    MATTE_WHITE = 0x20
    MATTE_CLEAR = 0x21
    MATTE_SILVER = 0x22
    SATIN_GOLD = 0x23
    SATIN_SILVER = 0x24
    BLUE_D = 0x30
    RED_D = 0x31
    FLUORESCENT_ORANGE = 0x40
    FLUORESCENT_YELLOW = 0x41
    BERRY_PINK_S = 0x50
    LIGHT_GRAY_S = 0x51
    LIME_GREEN_S = 0x52
    YELLOW_F = 0x60
    PINK_F = 0x61
    BLUE_F = 0x62
    WHITE_HEAT_SHRINK_TUBE = 0x70
    WHITE_FLEX_ID = 0x90
    YELLOW_FLEX_ID = 0x91
    CLEANING = 0xF0
    STENCIL = 0xF1
    INCOMPATIBLE = 0xFF


class TextColor(IntEnum):
    WHITE = 0x01
    OTHER = 0x02
    RED = 0x04
    BLUE = 0x05
    BLACK = 0x08
    GOLD = 0x0A
    BLUE_F = 0x62
    CLEANING = 0xF0
    STENCIL = 0xF1
    INCOMPATIBLE = 0XFF


@contextlib.contextmanager
def bt_socket_manager(*args, **kwargs):
    socket = bluetooth.BluetoothSocket(*args, **kwargs)

    yield socket

    socket.close()


def try_bt_connect(socket, bt_address, bt_channel) -> bool:
    try:
        socket.connect((bt_address, bt_channel))
    except BluetoothError as e:
        print(f"Unable to connect to printer {bt_address}: {e}")
        print("Please check the printer is on and properly paired in your system.")
        return False

    return True


def get_printer_info(bt_address, bt_channel):
    with bt_socket_manager(bluetooth.RFCOMM) as socket:
        try_bt_connect(socket, bt_address, bt_channel) or exit(1)

        send_invalidate(socket)
        send_initialize(socket)
        send_status_information_request(socket)

        status_information = receive_status_information_response(socket)
        handle_status_information(status_information)


def make_label(bt_address, bt_channel, image):
    with bt_socket_manager(bluetooth.RFCOMM) as socket:
        try_bt_connect(socket, bt_address, bt_channel) or exit(1)

        send_invalidate(socket)
        send_initialize(socket)
        send_status_information_request(socket)

        status_information = receive_status_information_response(socket)
        handle_status_information(status_information)

        width = TZE_DOTS.get(detected_media_width)

        if isinstance(image, list) and len(image):
            image = image[0]

        data = encode_png(image, width)

        send_switch_dynamic_command_mode(socket)
        send_switch_automatic_status_notification_mode(socket)
        send_print_information_command(socket, len(data), detected_media_width)
        send_various_mode_settings(socket)
        send_advanced_mode_settings(socket)
        send_specify_margin_amount(socket)
        send_select_compression_mode(socket)
        send_raster_data(socket, data)
        send_print_command(socket)
        send_raster_data(socket, data)
        send_print_command_with_feeding(socket)

        while True:
            status_information = receive_status_information_response(socket)
            handle_status_information(status_information)


def send_invalidate(socket: bluetooth.BluetoothSocket):
    """send 100 null bytes"""
    socket.send(b"\x00" * 100)


def send_initialize(socket: bluetooth.BluetoothSocket):
    """Send Initialization Code [1B 40]"""
    socket.send(b"\x1B\x40")


def send_switch_dynamic_command_mode(socket: bluetooth.BluetoothSocket):
    """set dynamic command mode to "raster mode" [1B 69 61 {01}]"""
    socket.send(b"\x1B\x69\x61\x01")


def send_switch_automatic_status_notification_mode(socket: bluetooth.BluetoothSocket):
    """set automatic status notification mode to "notify" [1B 69 21 {00}]"""
    socket.send(b"\x1B\x69\x21\x00")


def send_print_information_command(socket: bluetooth.BluetoothSocket, data_length: int, width):
    """
    Print to tape

    Command: [1B 69 7A {84 00 18 00 <data length 4 bytes> 00 00}]

    This is defined in the Brother Documentation under 'ESC i z Print information command'

    :param socket: The bluetooth socket to use
    :param data_length: The length of the data that will be sent
    :param width: Width of the tape used in mm. Defaults to 24mm
    """
    socket.send(b"\x1B\x69\x7A\x84\x00")
    socket.send(chr(width))  # n3 as per docs
    socket.send(b"\x00")  # n4
    socket.send((data_length >> 4).to_bytes(4, 'little'))
    socket.send(b"\x00\x00")


def send_various_mode_settings(socket: bluetooth.BluetoothSocket):
    """set to auto-cut, no mirror printing [1B 69 4D {40}]"""
    socket.send(b"\x1B\x69\x4D")
    socket.send(Mode.AUTO_CUT.to_bytes(1, "big"))


def send_advanced_mode_settings(socket: bluetooth.BluetoothSocket):
    """Set print chaining off [1B 69 4B {08}]"""
    # socket.send(b"\x1B\x69\x4B\x08")
    socket.send(b"\x1B\x69\x4B\x01")


def send_specify_margin_amount(socket: bluetooth.BluetoothSocket):
    """Set margin (feed) amount to 0 [1B 69 64 {00 00}]"""
    socket.send(b"\x1B\x69\x64\x00\x00")


def send_select_compression_mode(socket: bluetooth.BluetoothSocket):
    """Set to TIFF compression [4D {02}]"""
    socket.send(b"\x4D\x02")


def send_raster_data(socket: bluetooth.BluetoothSocket, data):
    """Send all raster data lines"""
    for line in rasterize(data):
        socket.send(bytes(line))


def send_print_command(socket: bluetooth.BluetoothSocket):
    socket.send(b"\x0C")

def send_print_command_with_feeding(socket: bluetooth.BluetoothSocket):
    """print and feed [1A]"""
    socket.send(b"\x1A")


def send_partial_cut(socket: bluetooth.BluetoothSocket):
    """Partial cut of label [1B 69 41 01]"""
    socket.send(b"\x1B\x69\x41\01")


def send_status_information_request(socket: bluetooth.BluetoothSocket):
    """request status information [1B 69 53]"""
    socket.send(b"\x1B\x69\x53")


def receive_status_information_response(socket: bluetooth.BluetoothSocket):
    """receive status information"""
    response = socket.recv(32)

    if len(response) != 32:
        sys.exit("Expected 32 bytes, but only received %d" % len(response))

    return response


def handle_status_information(status_information):
    def handle_reply_to_status_request(status_information):
        global detected_media_width
        print("Printer Status")
        print("--------------")
        print("Media Width: %dmm" % status_information[STATUS_OFFSET_MEDIA_WIDTH])
        print("Media Type: %s" % MediaType(status_information[STATUS_OFFSET_MEDIA_TYPE]).name)
        print("Tape Color: %s" % TapeColor(status_information[STATUS_OFFSET_TAPE_COLOR_INFORMATION]).name)
        print("Text Color: %s" % TextColor(status_information[STATUS_OFFSET_TEXT_COLOR_INFORMATION]).name)
        print()

        detected_media_width = status_information[STATUS_OFFSET_MEDIA_WIDTH]

    def handle_printing_completed(status_information):
        print("Printing Completed")
        print("------------------")

        mode = Mode(status_information[STATUS_OFFSET_MODE])

        print("Mode: %s" % ", ".join(str(f.name) for f in Mode if f in mode))

        sys.exit(0)

    def handle_error_occurred(status_information):
        print("Error Occurred")
        print("--------------")

        error_information_1 = ErrorInformation1(status_information[STATUS_OFFSET_ERROR_INFORMATION_1])
        error_information_2 = ErrorInformation2(status_information[STATUS_OFFSET_ERROR_INFORMATION_2])

        print("Error information 1: %s" % ", ".join(str(f.name) for f in ErrorInformation1 if f in error_information_1))
        print("Error information 2: %s" % ", ".join(str(f.name) for f in ErrorInformation2 if f in error_information_2))

        sys.exit("An error has occurred; exiting program")

    def handle_turned_off(status_information):
        print("Turned Off")
        print("----------")

        sys.exit("Device was turned off")

    def handle_notification(status_information):
        print("Notification")
        print("------------")
        print(f"Notification number: {NotificationNumber(status_information[STATUS_OFFSET_NOTIFICATION_NUMBER]).name}")
        print()

    def handle_phase_change(status_information):
        print("Phase Changed")
        print("-------------")

        phase_type = status_information[STATUS_OFFSET_PHASE_TYPE]
        phase_number = int.from_bytes(status_information[STATUS_OFFSET_PHASE_NUMBER:STATUS_OFFSET_PHASE_NUMBER + 2],
                                      "big")

        print("Phase type: %s" % PhaseType(phase_type).name)
        print("Phase number: %s" % (PhaseNumberPrintingState(
            phase_number) if phase_type == PhaseType.PRINTING_STATE else PhaseNumberEditingState(phase_number)).name)
        print()

    handlers = {
        StatusType.REPLY_TO_STATUS_REQUEST: handle_reply_to_status_request,
        StatusType.PRINTING_COMPLETED: handle_printing_completed,
        StatusType.ERROR_OCCURRED: handle_error_occurred,
        StatusType.TURNED_OFF: handle_turned_off,
        StatusType.NOTIFICATION: handle_notification,
        StatusType.PHASE_CHANGE: handle_phase_change
    }

    status_type = status_information[STATUS_OFFSET_STATUS_TYPE]

    handlers[status_type](status_information)


def bad_options(message):
    print(f"Error: {message}. Use {sys.argv[0]} --help to get more information")
    exit(1)


def main():
    options = app_args.parse()

    if options.set_default:
        if not options.bt_address:
            bad_options('You must provide a BT address to set as default')
        else:
            set_default_bt(options.bt_address)
            print(f"{options.bt_address} set as default BT address")

    if not options.info and not options.image and not options.set_default:
        bad_options('Image path required')

    if not options.bt_address:
        default_bt = get_default_bt()
        if not default_bt:
            bad_options("BT Address is required. If you'd like to remember it use --set-default")
        options.bt_address = default_bt
        print(f"Connecting to printer with BT Address of {options.bt_address}")

    if options.info:
        get_printer_info(options.bt_address, options.bt_channel)
        exit(0)

    if options.image:
        make_label(options.bt_address, options.bt_channel, options.image)


if __name__ == "__main__":
    main()
