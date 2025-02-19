from enum import IntFlag, IntEnum


class AdvancedMode(IntFlag):
    """ Advanced mode settings ESC i K"""
    DEFAULTS = 0
    NO_CHAIN_PRINT = 1 << 3
    SPECIAL_TAPE = 1 << 4       # Labels are not cut when special tape is installed
    HIGH_RESOLUTION = 1 << 6
    NO_BUFFER_CLEARING = 1 << 7


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


class StatusOffset(IntEnum):
    ERROR_INFORMATION_1 = 8
    ERROR_INFORMATION_2 = 9
    MEDIA_WIDTH = 10
    MEDIA_TYPE = 11
    MODE = 15
    MEDIA_LENGTH = 17
    STATUS_TYPE = 18
    PHASE_TYPE = 19
    PHASE_NUMBER = 20
    NOTIFICATION_NUMBER = 22
    TAPE_COLOR_INFORMATION = 24
    TEXT_COLOR_INFORMATION = 25
    HARDWARE_SETTINGS = 26

# Map the size of tape to the number of dots on the print area
TZE_DOTS = {
    3: 24,  # Actually 3.5mm, not sure how this is reported if its 3 or 4
    6: 32,
    9: 50,
    12: 70,
    18: 112,
    24: 128
}
