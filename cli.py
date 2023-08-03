import argparse
import logging
import pprint
import time
import arduboy.device
import arduboy.file
import arduboy.serial

ACTIONS = [
    "scan",
    "upload"
]

VERSION = "0.0.1"
GRACEFULSTOPSECONDS = 0.3 # Why though? Was 3: reduced to 0.3


def create_parser():
    parser = argparse.ArgumentParser(prog="arduboy_toolset", description='Tools for working with Arduboy')
    parser.add_argument("action", choices=ACTIONS, help="Tool/action to perform")
    parser.add_argument("-i", "--input_file", help="Input file for given command")
    parser.add_argument("-o", "--output_file", help="Output file for given command")
    parser.add_argument("-m", "--multi", action="store_true", help="Enable multi-device-mode (where applicable)")
    parser.add_argument("--debug", action="store_true", help="Enable extra debugging output (useful for error handling)")
    parser.add_argument("--SSD1309", action="store_true", help="Enable patching for SSD1309 displays (arduboy upload)")
    parser.add_argument("--microled", action="store_true", help="Enable patching for Arduino Micro LED polarity (arduboy upload)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser

def run(args):
    if args.action == "scan":
        scan_action(args)
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

def scan_action(args):
    pp = pprint.PrettyPrinter()
    devices = arduboy.device.get_connected_devices()
    print(f"Found {len(devices)} devices:")
    pp.pprint(devices)

# -------------------------
#    HANDLING NONSENSE!
# -------------------------

# Mr.Blinky's scripts had some time for exiting. I assumed it was to read the screen, but just
# in case, I have also included a small timeout here too. If I get confirmation the exit time
# is just to read printed output, I will reduce the time further.
def graceful_stop(s_port):
    print(f"<<< Exiting bootloader on {s_port.port}...")
    arduboy.serial.exit_bootloader(s_port)
    time.sleep(GRACEFULSTOPSECONDS)
