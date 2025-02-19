import sys

import app_args
from config import set_default_bt, get_default_bt
from enums import AdvancedMode
from pt710bt import PT710BT


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
        with PT710BT(options.bt_address, options.bt_channel) as pt:
            pt.get_printer_info()
        exit(0)

    if options.image:
        advanced_mode: AdvancedMode = AdvancedMode.DEFAULTS

        if not options.chain:
            advanced_mode |= AdvancedMode.NO_CHAIN_PRINT
        if options.hi_res:
            advanced_mode |= AdvancedMode.HIGH_RESOLUTION

        with PT710BT(options.bt_address, options.bt_channel) as pt:
            pt.print_labels(options.image, advanced_mode)


if __name__ == "__main__":
    main()
