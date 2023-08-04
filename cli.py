import argparse
import logging
import pprint
import time
import arduboy.device
import arduboy.file
import arduboy.serial

ACTIONS = [
    "scan",
    "upload",
    "eeprombackup",
    "eepromrestore",
    "eepromerase",
    "fxbackup",
    "fxupload"
]

VERSION = "0.0.1"
GRACEFULSTOPSECONDS = 0.3 # Why though? Was 3: reduced to 0.3


def create_parser():
    parser = argparse.ArgumentParser(prog="arduboy_toolset", description='Tools for working with Arduboy using Mr.Blinky\'s original code')
    parser.add_argument("action", choices=ACTIONS, help="Tool/action to perform")
    parser.add_argument("-i", "--input_file", help="Input file for given command")
    parser.add_argument("-o", "--output_file", help="Output file for given command")
    parser.add_argument("-m", "--multi", action="store_true", help="Enable multi-device-mode (where applicable)")
    parser.add_argument("-t", "--trim", action="store_true", help="Trim backups where applicable (usually fx data)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--debug", action="store_true", help="Enable extra debugging output (useful for error handling)")
    parser.add_argument("--SSD1309", action="store_true", help="Enable patching for SSD1309 displays (where applicable)")
    parser.add_argument("--microled", action="store_true", help="Enable patching for Arduino Micro LED polarity (where applicable)")
    return parser

def run(args):
    if args.action == "scan":
        scan_action(args)
    elif args.action == "upload":
        upload_action(args)
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

def get_arduhex(args):
    infile = get_required_input(args)
    records = arduboy.file.read_arduhex(infile)
    parsed = arduboy.file.parse_arduhex(records)
    if args.SSD1309:
        if parsed.patch_ssd1309():
            logging.info("Patching upload for SSD1309")
        else:
            logging.warning("Flagged for SSD1309 parsing but no LCD boot program found! Not patched!")
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
    print(f"Progress: {progress:05.2f}% {bar}", end="\r", flush=True)
    if current == total:
        print(f"Complete! {current}/{total}")

def work_per_device(args, work):
    devices = get_devices(args)
    for d in devices:
        print(f">>> Working on device {d}")
        s_port = d.connect_serial()
        try:
            work(s_port)
        except Exception as ex:
            print(f" ** SKIPPING DEVICE {d} DUE TO ERROR: {ex}")
        finally:
            graceful_stop(s_port)


# ---------------------
#   CLI ACTIONS !!
# ---------------------

def scan_action(args):
    pp = pprint.PrettyPrinter()
    devices = arduboy.device.get_connected_devices()
    print(f"Found {len(devices)} devices:")
    pp.pprint(devices)

def upload_action(args):
    parsed = get_arduhex(args)
    # Define the work to do per device then send it off to the generic function. The handler
    # ensures all actions that perform work on multiple devices have the same output format.
    def do_work(s_port):
        if parsed.overwrites_caterina and arduboy.serial.is_caterina(s_port):
            raise Exception("Upload will likely corrupt the bootloader.")
        arduboy.serial.flash_arduhex(parsed, s_port, basic_reporting) 
        arduboy.serial.verify_arduhex(parsed, s_port, basic_reporting) 
    work_per_device(args, do_work)

def fxupload_action(args):
    infile = get_required_input(args)
    raise Exception("Not implemented yet!")
    # parsed = get_arduhex(args)
    # Define the work to do per device then send it off to the generic function. The handler
    # ensures all actions that perform work on multiple devices have the same output format.
    def do_work(s_port):
        # For now, can't disable verification on fx uploads (same as arduhex, actually)
        arduboy.serial.flash_fx(infile, 0, s_port, True, basic_reporting)
    work_per_device(args, do_work)

def fxbackup_action(args):
    outfile = args.output_file if args.output_file else time.strftime("fx-backup-%Y%m%d-%H%M%S.bin", time.localtime())
    device = 1
    def do_work(s_port):
        nonlocal device
        # Not the most elegant way to do this, I might change it later
        real_outfile = outfile if device == 1 else f"{device}-{outfile}"
        device += 1
        arduboy.serial.backup_fx(s_port, real_outfile, basic_reporting)
        if args.trim:
            arduboy.file.trim_fx_cart_file(real_outfile)
    work_per_device(args, do_work)

def eeprom_backup_action(args):
    outfile = args.output_file if args.output_file else time.strftime("eeprom-backup-%Y%m%d-%H%M%S.bin", time.localtime())
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
    work_per_device(args, do_work)

def eeprom_erase_action(args):
    def do_work(s_port):
        logging.info(f"Erasing eeprom in {s_port.port}")
        arduboy.serial.erase_eeprom(s_port)
    work_per_device(args, do_work)

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
