import logging
import sys
import arduboy
import pprint
import gui
import cli

pp = pprint.PrettyPrinter()

def main():

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run the UI if no arguments are passed
    if len(sys.argv) == 1:
        (app, window) = gui.make_app()
        window.show()
        sys.exit(app.exec_())

    # Otherwise, let's parse some arguments!
    parser = cli.create_parser()
    args = parser.parse_args()

    if args.action == "scan":
        devices = arduboy.get_connected_devices()
        print(f"Found {len(devices)} devices:")
        pp.pprint(devices)
    elif args.action == "upload":
        devices = get_devices(args)
    else:
        print(f"Unknown command {args.action}")

    # NOTE: going to have two modes: multimode and single mode. In single mode, it will automatically
    # reset the arduboy (using arduboy.disconnect_device) and wait for SOMETHING to show up again. 
    # In multimode, it will simply perform the given action on all connected devices that have a bootloader
    # (will NOT try to reset any that don't)


# Whether single or multi is supplied, return a list of bootloader-ready device(s).
def get_devices(args):
    devices = []
    if args.multi:
        logging.info("Multimode set, running command on all connected (bootloader) devices")
        devices = arduboy.get_connected_devices(bootloader_only=True)
        if len(devices) == 0:
            raise Exception("No connected arduboys in bootloader mode!")
        return devices
    else:
        logging.debug("Finding single arduboy device in bootloader mode")
        devices = [ arduboy.find_single() ]
    print("------------------------------------")
    print("Operating on the following devices: ")
    print("------------------------------------")
    for d in devices:
        print(f"* {d}")
    return devices


if __name__ == "__main__":
    main()