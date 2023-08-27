import argparse
import logging
import pprint
import sys
import traceback
import arduboy.device
import arduboy.serial
import arduboy.arduhex
import arduboy.fxcart
import arduboy.patch
import constants
import utils

ACTIONS = [
    "scan",
    "sketchupload",
    "sketchbackup",
    "eeprombackup",
    "eepromrestore",
    "eepromerase",
    "fxbackup",
    "fxupload"
]

SHOWTRACE = False # Although this is capitalized like a constant, the value is set from the argument list

def create_parser():
    parser = argparse.ArgumentParser(prog="arduboy_toolset", description='Tools for working with Arduboy using Mr.Blinky\'s original code')
    parser.add_argument("action", choices=ACTIONS, help="Tool/action to perform")
    parser.add_argument("-i", "--input_file", help="Input file for given command")
    parser.add_argument("-o", "--output_file", help="Output file for given command")
    parser.add_argument("-m", "--multi", action="store_true", help="Enable multi-device-mode (where applicable)")
    parser.add_argument("-t", "--trim", action="store_true", help="Trim backups where applicable (usually fx data)")
    parser.add_argument("--pagenum", type=int, help="Set starting pagenumber (where appropriate, such as fx cart)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {constants.VERSION}")
    parser.add_argument("--debug", action="store_true", help="Enable extra debugging output (useful for error handling)")
    parser.add_argument("--SSD1309", action="store_true", help="Enable patching for SSD1309 displays (where applicable)")
    parser.add_argument("--microled", action="store_true", help="Enable patching for Arduino Micro LED polarity (where applicable)")
    parser.add_argument("--include_bootloader", action="store_true", help="Include bootloader in backup (where applicable: sketch)")
    return parser


# Main entry point!
def main():
    global SHOWTRACE

    # Some initial setup
    sys.excepthook = custom_excepthook
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = create_parser()
    args = parser.parse_args()
    SHOWTRACE = args.debug

    if args.action == "scan":
        scan_action(args)
    elif args.action == "sketchupload":
        sketchupload_action(args)
    elif args.action == "sketchbackup":
        sketchbackup_action(args)
    elif args.action == "fxupload":
        fxupload_action(args)
    elif args.action == "fxbackup":
        fxbackup_action(args)
    elif args.action == "eeprombackup":
        eeprom_backup_action(args)
    elif args.action == "eepromrestore":
        eeprom_restore_action(args)
    elif args.action == "eepromerase":
        eeprom_erase_action(args)
    else:
        print(f"Unknown command {args.action}")


# Custom exception handler to make error information less ugly for most users
def custom_excepthook(exc_type, exc_value, exc_traceback):
    print(" ** UNHANDLED EXCEPTION: " + str(exc_value)) # .args[0])
    if SHOWTRACE:
        print(f"Type: {exc_type}")
        print(f"Traceback: ")
        traceback.print_tb(exc_traceback)


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
        raise Exception("Input file required! Use -i <file> or --input_file <file>")
    return args.input_file

def get_required_output(args):
    if not args.output_file:
        raise Exception("Output file required! Use -o <file> or --output_file <file>")
    return args.output_file

def basic_reporting(current, total):
    progress = (current / total) * 100 # progress in percent
    bar_length = 30
    num_blocks = int(bar_length * progress / 100)
    bar = "[" + "#" * num_blocks + "-" * (bar_length - num_blocks) + "]"
    print(f"Progress: {progress:05.2f}% {bar}", end="\r", flush=True)
    if current == total:
        complete_text = f"{current}/{total}".ljust(6) # 6 for the 5 digits of percent + the percent sign
        print(f"Complete! {complete_text} {bar}")

def work_per_device(args, work, exit_bootloaoder = False):
    devices = get_devices(args)
    for d in devices:
        print(f">>> Working on device {d}")
        s_port = d.connect_serial()
        try:
            work(s_port)
        except Exception as ex:
            print(f" ** SKIPPING DEVICE {d} DUE TO ERROR: {ex}")
        finally:
            print(f"<<< Disconnecting device on {s_port.port}...")
            if exit_bootloaoder:
                arduboy.serial.exit_bootloader(s_port)
            else:
                arduboy.serial.exit_normal(s_port)


# ---------------------
#   CLI ACTIONS !!
# ---------------------

def scan_action(args):
    pp = pprint.PrettyPrinter()
    devices = arduboy.device.get_connected_devices()
    print(f"Found {len(devices)} devices:")
    pp.pprint(devices)

def sketchupload_action(args):
    infile = get_required_input(args)
    pard = arduboy.arduhex.read(infile)
    parsed = arduboy.arduhex.parse(pard)
    if args.SSD1309:
        if arduboy.patch.patch_all_screen(parsed.flash_data, ssd1309=True):
            logging.info("Patched upload for SSD1309")
        else:
            logging.warning("Flagged for SSD1309 patching but no LCD boot program found! Not patched!")
    if args.microled:
        arduboy.patch.patch_microled(parsed.flash_data)
        logging.info("Patched upload for Arduino Micro LED polarity")
    logging.debug(f"Info on hex file: {parsed.flash_page_count} pages, is_caterina: {parsed.overwrites_caterina}")
    # Define the work to do per device then send it off to the generic function. The handler
    # ensures all actions that perform work on multiple devices have the same output format.
    def do_work(s_port):
        if parsed.overwrites_caterina and arduboy.serial.is_caterina(s_port):
            raise Exception("Upload will likely corrupt the bootloader.")
        arduboy.serial.flash_arduhex(parsed, s_port, basic_reporting) 
        arduboy.serial.verify_arduhex(parsed, s_port, basic_reporting) 
    work_per_device(args, do_work, True)

def sketchbackup_action(args):
    outfile = args.output_file if args.output_file else utils.get_sketch_backup_filename()
    device = 1
    def do_work(s_port):
        nonlocal device
        # Not the most elegant way to do this, I might change it later
        real_outfile = outfile if device == 1 else f"{device}-{outfile}"
        device += 1
        sketchdata = arduboy.serial.backup_sketch(s_port, args.include_bootloader)
        logging.info(f"Saving sketch backup ({len(sketchdata)} bytes) to {real_outfile}")
        with open (real_outfile,"wb") as f:
            f.write(sketchdata)
    work_per_device(args, do_work)

def fxupload_action(args):
    infile = get_required_input(args)
    flashbytes = arduboy.fxcart.read(infile)
    if args.SSD1309:
        count = arduboy.patch.patch_all_screen(flashbytes, ssd1309=True)
        if count:
            logging.info(f"Patched {count} programs in cart for SSD1309")
        else:
            logging.warning("Flagged for SSD1309 patching but not a single LCD boot program found! Not patched!")
    if args.microled:
        logging.warning("Micro LED polarity patching not available (yet?) for FX carts!")
    if args.pagenum:
        pagenum = args.pagenum
        logging.info(f"Overriding starting page for fx to {pagenum}")
    else:
        pagenum = 0
    # Define the work to do per device then send it off to the generic function. The handler
    # ensures all actions that perform work on multiple devices have the same output format.
    def do_work(s_port):
        # For now, can't disable verification on fx uploads (same as arduhex, actually)
        arduboy.serial.flash_fx(flashbytes, pagenum, s_port, True, basic_reporting)
    work_per_device(args, do_work)

def fxbackup_action(args):
    outfile = args.output_file if args.output_file else utils.get_fx_backup_filename()
    device = 1
    def do_work(s_port):
        nonlocal device
        # Not the most elegant way to do this, I might change it later
        real_outfile = outfile if device == 1 else f"{device}-{outfile}"
        device += 1
        bindata = arduboy.serial.backup_fx(s_port, basic_reporting)
        if args.trim:
            bindata = arduboy.fxcart.trim(bindata)
        with open (real_outfile,"wb") as f:
            f.write(bindata)
    work_per_device(args, do_work)

def eeprom_backup_action(args):
    outfile = args.output_file if args.output_file else utils.get_eeprom_backup_filename()
    device = 1
    def do_work(s_port):
        nonlocal device
        # Not the most elegant way to do this, I might change it later
        real_outfile = outfile if device == 1 else f"{device}-{outfile}"
        device += 1
        logging.info(f"Backing up eeprom from {s_port.port} into {real_outfile}")
        eepromdata = arduboy.serial.read_eeprom(s_port)
        with open (real_outfile,"wb") as f:
            f.write(eepromdata)
    work_per_device(args, do_work)

def eeprom_restore_action(args):
    infile = get_required_input(args)
    with open (infile,"rb") as f:
        eepromdata = bytearray(f.read())
    def do_work(s_port):
        logging.info(f"Restoring eeprom from {infile} into {s_port.port}")
        arduboy.serial.write_eeprom(eepromdata, s_port)
    work_per_device(args, do_work, True) # Since this is save data, probably should reset or something

def eeprom_erase_action(args):
    def do_work(s_port):
        logging.info(f"Erasing eeprom in {s_port.port}")
        arduboy.serial.erase_eeprom(s_port)
    work_per_device(args, do_work, True) # Since this is save data, probably should reset or something

# -------------------------
#    HANDLING NONSENSE!
# -------------------------

if __name__ == "__main__":
    main()