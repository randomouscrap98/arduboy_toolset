import logging
import sys
import pprint
import gui
import cli
import os
import arduboy.device
import arduboy.file
import traceback

SHOWTRACE = False # Although this is capitalized like a constant, the value is set from the argument list

# Main entry point!
def main():

    global SHOWTRACE

    # Some initial setup
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.excepthook = custom_excepthook
    pp = pprint.PrettyPrinter()

    # Run the UI if no arguments are passed
    if len(sys.argv) == 1:
        (app, window) = gui.make_app()
        window.show()
        sys.exit(app.exec_())

    # Otherwise, let's parse some arguments and run the CLI version!
    parser = cli.create_parser()
    args = parser.parse_args()
    SHOWTRACE = args.debug

    if args.action == "scan":
        devices = arduboy.device.get_connected_devices()
        print(f"Found {len(devices)} devices:")
        pp.pprint(devices)
    elif args.action == "upload":
        devices = get_devices(args)
        infile = get_required_input(args)
        arduboy.file.read_arduhex(infile)
    else:
        print(f"Unknown command {args.action}")


# Whether single or multi is supplied, return a list of bootloader-ready device(s).
def get_devices(args):
    devices = []
    if args.multi:
        logging.info("Multimode set, running command on all connected (bootloader) devices")
        devices = arduboy.device.get_connected_devices(bootloader_only=True)
        if len(devices) == 0:
            raise Exception("No connected arduboys in bootloader mode!")
    else:
        logging.debug("Finding single arduboy device in bootloader mode")
        devices = [ arduboy.device.find_single() ]
    print("------------------------------------")
    print("Operating on the following devices: ")
    print("------------------------------------")
    for d in devices:
        print(f"* {d}")
    return devices

def get_required_input(args):
    if not args.input_file:
        raise Exception("Input file required! Use -i <file> or --input <file>")
    return args.input_file

# Custom exception handler to make error information less ugly for most users
def custom_excepthook(exc_type, exc_value, exc_traceback):
    print(" ** UNHANDLED EXCEPTION: " + exc_value.args[0])
    if SHOWTRACE:
        print(f"Type: {exc_type}")
        print(f"Traceback: ")
        traceback.print_tb(exc_traceback)


if __name__ == "__main__":
    main()