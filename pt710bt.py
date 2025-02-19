from sys import stderr
from typing import List

import bluetooth
from bluetooth import BluetoothError

from enums import StatusOffset, MediaType, TapeColor, TextColor, Mode, ErrorInformation1, ErrorInformation2, \
    NotificationNumber, PhaseType, PhaseNumberPrintingState, PhaseNumberEditingState, StatusType, TZE_DOTS, AdvancedMode
from rasterizer import encode_png, rasterize


class PT710BT:
    def __init__(self, bt_address: str, bt_channel:int = 1):
        self.bt_address = bt_address
        self.bt_channel = bt_channel
        self.last_media_width = -1
        self._in = False

    def __enter__(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self._in = True

        try:
            self.socket.connect((self.bt_address, self.bt_channel))
        except BluetoothError as e:
            print(f"Unable to connect to printer {self.bt_address} (Chan {self.bt_channel}): {e}")
            print("Please check the printer is on and properly paired in your system.")
            raise

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()
        self._in = False

    def get_printer_info(self) -> None | int:
        self.send_invalidate()
        self.send_initialize()
        self.send_status_information_request()

        status_information = self.receive_status_information_response()
        return self.handle_status_information(status_information)

    def print_label(self, image: str, advanced_mode: AdvancedMode = AdvancedMode.NO_CHAIN_PRINT):
        self.print_labels([image], advanced_mode)

    def print_labels(self, images: List[str], advanced_mode: AdvancedMode = AdvancedMode.NO_CHAIN_PRINT):
        self.send_invalidate()
        self.send_initialize()
        self.send_status_information_request()

        # Populates media info
        status_information = self.receive_status_information_response()
        result = self.handle_status_information(status_information)
        if result:
            exit(result)

        width = TZE_DOTS.get(self.last_media_width)

        data_list = []
        for i in images:
            data_list.append(encode_png(i, width))

        data = data_list.pop(0)
        self.send_switch_dynamic_command_mode()
        self.send_switch_automatic_status_notification_mode()
        self.send_print_information_command(len(data), self.last_media_width)
        self.send_various_mode_settings()
        self.send_advanced_mode_settings(advanced_mode)
        self.send_specify_margin_amount()
        self.send_select_compression_mode()
        self.send_raster_data(data)

        while data_list:
            self.send_print_command()
            data = data_list.pop(0)
            self.send_raster_data(data)

        self.send_print_command_with_feeding()

        done = None
        while done is None:
            status_information = self.receive_status_information_response()
            done = self.handle_status_information(status_information)

    def send_invalidate(self):
        """send 100 null bytes"""
        self.socket.send(b"\x00" * 100)

    def send_initialize(self):
        """Send Initialization Code [1B 40]"""
        self.socket.send(b"\x1B\x40")

    def send_switch_dynamic_command_mode(self):
        """set dynamic command mode to "raster mode" [1B 69 61 {01}]"""
        self.socket.send(b"\x1B\x69\x61\x01")

    def send_switch_automatic_status_notification_mode(self):
        """set automatic status notification mode to "notify" [1B 69 21 {00}]"""
        self.socket.send(b"\x1B\x69\x21\x00")

    def send_status_information_request(self):
        """request status information [1B 69 53]"""
        self.socket.send(b"\x1B\x69\x53")

    def send_various_mode_settings(self):
        """set to auto-cut, no mirror printing [1B 69 4D {40}]"""
        self.socket.send(b"\x1B\x69\x4D")
        self.socket.send(Mode.AUTO_CUT.to_bytes(1, "big"))

    def send_advanced_mode_settings(self, mode: AdvancedMode):
        """Set advanced modes (e.g. Chain print)[1B 69 4B {xx}]"""
        # socket.send(b"\x1B\x69\x4B\x08") <-- That's no chain
        self.socket.send(b"\x1B\x69\x4B")
        self.socket.send(mode.to_bytes(1, "big"))

    def send_specify_margin_amount(self):
        """Set margin (feed) amount to 0 [1B 69 64 {00 00}]"""
        self.socket.send(b"\x1B\x69\x64\x00\x00")

    def send_select_compression_mode(self):
        """Set to TIFF compression [4D {02}]"""
        self.socket.send(b"\x4D\x02")

    def send_raster_data(self, data):
        """Send all raster data lines"""
        for line in rasterize(data):
            self.socket.send(bytes(line))

    def send_print_command(self):
        self.socket.send(b"\x0C")

    def send_print_command_with_feeding(self):
        """print and feed [1A]"""
        self.socket.send(b"\x1A")

    def send_print_information_command(self, data_length: int, width):
        """
        Print to tape

        Command: [1B 69 7A {84 00 18 00 <data length 4 bytes> 00 00}]

        This is defined in the Brother Documentation under 'ESC i z Print information command'

        :param socket: The bluetooth socket to use
        :param data_length: The length of the data that will be sent
        :param width: Width of the tape used in mm. Defaults to 24mm
        """
        self.socket.send(b"\x1B\x69\x7A\x84\x00")
        self.socket.send(chr(width))  # n3 as per docs
        self.socket.send(b"\x00")  # n4
        self.socket.send((data_length >> 4).to_bytes(4, 'little'))
        self.socket.send(b"\x00\x00")

    def receive_status_information_response(self):
        """receive status information"""
        response = self.socket.recv(32)

        if len(response) != 32:
            raise Exception("Expected 32 bytes, but only received %d" % len(response))

        return response

    def handle_status_information(self, printer_status_information) -> None | int:
        def handle_reply_to_status_request(status_information):
            print("Printer Status")
            print("--------------")
            print("Media Width: %dmm" % status_information[StatusOffset.MEDIA_WIDTH])
            print("Media Type: %s" % MediaType(status_information[StatusOffset.MEDIA_TYPE]).name)
            print("Tape Color: %s" % TapeColor(status_information[StatusOffset.TAPE_COLOR_INFORMATION]).name)
            print("Text Color: %s" % TextColor(status_information[StatusOffset.TEXT_COLOR_INFORMATION]).name)
            print()

            self.last_media_width = status_information[StatusOffset.MEDIA_WIDTH]

        def handle_printing_completed(status_information):
            print("Printing Completed")
            print("------------------")

            mode = Mode(status_information[StatusOffset.MODE])

            print("Mode: %s" % ", ".join(str(f.name) for f in Mode if f in mode))

            return 0

        def handle_error_occurred(status_information):
            print("Error Occurred")
            print("--------------")

            error_information_1 = ErrorInformation1(status_information[StatusOffset.ERROR_INFORMATION_1])
            error_information_2 = ErrorInformation2(status_information[StatusOffset.ERROR_INFORMATION_2])

            print("Error information 1: %s" % ", ".join(
                str(f.name) for f in ErrorInformation1 if f in error_information_1))
            print("Error information 2: %s" % ", ".join(
                str(f.name) for f in ErrorInformation2 if f in error_information_2))

            print("An error has occurred; exiting program", file=stderr)

            return 1

        def handle_turned_off(status_information):
            print("Turned Off")
            print("----------")

            print("Device was turned off", file=stderr)
            return 2

        def handle_notification(status_information):
            print("Notification")
            print("------------")
            print(f"Notification number: {NotificationNumber(status_information[StatusOffset.NOTIFICATION_NUMBER]).name}")
            print()

        def handle_phase_change(status_information):
            print("Phase Changed")
            print("-------------")

            phase_type = status_information[StatusOffset.PHASE_TYPE]
            phase_number = int.from_bytes(status_information[StatusOffset.PHASE_NUMBER:StatusOffset.PHASE_NUMBER + 2],
                                          "big")

            print("Phase type: ", PhaseType(phase_type).name)
            phase_state = PhaseNumberPrintingState(phase_number) if phase_type == PhaseType.PRINTING_STATE else PhaseNumberEditingState(phase_number).name
            print(f"Phase state: {phase_state}")
            print()

        handlers = {
            StatusType.REPLY_TO_STATUS_REQUEST: handle_reply_to_status_request,
            StatusType.PRINTING_COMPLETED: handle_printing_completed,
            StatusType.ERROR_OCCURRED: handle_error_occurred,
            StatusType.TURNED_OFF: handle_turned_off,
            StatusType.NOTIFICATION: handle_notification,
            StatusType.PHASE_CHANGE: handle_phase_change
        }

        status_type = printer_status_information[StatusOffset.STATUS_TYPE]

        return handlers[status_type](printer_status_information)

