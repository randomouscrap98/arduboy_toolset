import sys
import arduboy
import pprint
import gui
import cli

def main():

    # Run the UI if no arguments are passed
    if len(sys.argv) == 1:
        app = gui.make_app()
        sys.exit(app.exec_())

    # Otherwise, let's parse some arguments!
    parser = cli.create_parser()
    args = parser.parse_args()

    if args.action == "scan":
        devices = arduboy.get_connected_devices()
        pp = pprint.PrettyPrinter()
        print(f"Found {len(devices)} devices:")
        pp.pprint(devices)
    else:
        print(f"Unknown command {args.action}")

    # NOTE: going to have two modes: multimode and single mode. In single mode, it will automatically
    # reset the arduboy (using arduboy.disconnect_device) and wait for SOMETHING to show up again. 
    # In multimode, it will simply perform the given action on all connected devices that have a bootloader
    # (will NOT try to reset any that don't)



if __name__ == "__main__":
    main()