import logging
import sys
import pprint
import gui
import cli
import time
import arduboy.device
import arduboy.file
import arduboy.serial
import traceback
import math

SHOWTRACE = False # Although this is capitalized like a constant, the value is set from the argument list
GRACEFULSTOPSECONDS = 0.3 # Why though? Was 3: reduced to 0.3

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
        upload_action(args)
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

def get_arduhex(args):
    infile = get_required_input(args)
    records = arduboy.file.read_arduhex(infile)
    parsed = arduboy.file.parse_arduhex(records)
    if args.SSD1309:
        if parsed.patch_ssd1309():
            logging.info("Patching upload for SSD1309")
        else:
            logging.info("Flagged for SSD1309 parsing but no LCD boot program found! Not patched!")
    if args.microled:
        parsed.patch_microled()
        logging.info("Patched upload for Arduino Micro LED polarity")
    
    logging.debug(f"Info on hex file: {parsed.flash_page_count} pages, is_caterina: {parsed.overwrites_caterina}")
    return parsed

def basic_reporting(current, total):
    # report_per = math.ceil(total / 50) # We'll display up to 50 total elements
    progress = (current / total) * 100 # progress in percent
    bar_length = 30
    num_blocks = int(bar_length * progress / 100)
    bar = "[" + "#" * num_blocks + "-" * (bar_length - num_blocks) + "]"
    print(f"Progress: {progress:.2f}% {bar}", end="\r", flush=True)
    if current == total:
        print(f"Complete! {current}/{total}")

# ---------------------
#   CLI ACTIONS !!
# ---------------------

def upload_action(args):
    parsed = get_arduhex(args)
    devices = get_devices(args)
    for d in devices:
        print(f">>> Working on device {d}")
        s_port = d.connect_serial()
        try:
            if parsed.overwrites_caterina and arduboy.serial.is_caterina(s_port):
                raise Exception("Upload will likely corrupt the bootloader.")
            arduboy.serial.flash_arduhex(parsed, s_port, basic_reporting) 
            arduboy.serial.verify_arduhex(parsed, s_port, basic_reporting) 
        except Exception as ex:
            print(f" ** SKIPPING DEVICE {d} DUE TO ERROR: {ex}")
        finally:
            graceful_stop(s_port)


# -------------------------
#    HANDLING NONSENSE!
# -------------------------

# Custom exception handler to make error information less ugly for most users
def custom_excepthook(exc_type, exc_value, exc_traceback):
    print(" ** UNHANDLED EXCEPTION: " + str(exc_value)) # .args[0])
    if SHOWTRACE:
        print(f"Type: {exc_type}")
        print(f"Traceback: ")
        traceback.print_tb(exc_traceback)

# Mr.Blinky's scripts had some time for exiting. I assumed it was to read the screen, but just
# in case, I have also included a small timeout here too. If I get confirmation the exit time
# is just to read printed output, I will reduce the time further.
def graceful_stop(s_port):
    print(f"<<< Exiting bootloader on {s_port.port}...")
    arduboy.serial.exit_bootloader(s_port)
    time.sleep(GRACEFULSTOPSECONDS)

if __name__ == "__main__":
    main()