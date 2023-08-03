import logging
import sys
import gui
import cli
import traceback

SHOWTRACE = False # Although this is capitalized like a constant, the value is set from the argument list

# Main entry point!
def main():

    global SHOWTRACE

    # Some initial setup
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.excepthook = custom_excepthook

    # Run the UI if no arguments are passed
    if len(sys.argv) == 1:
        (app, window) = gui.make_app()
        window.show()
        sys.exit(app.exec_())

    # Otherwise, let's parse some arguments and run the CLI version!
    parser = cli.create_parser()
    args = parser.parse_args()
    SHOWTRACE = args.debug
    cli.run(args)

# Custom exception handler to make error information less ugly for most users
def custom_excepthook(exc_type, exc_value, exc_traceback):
    print(" ** UNHANDLED EXCEPTION: " + str(exc_value)) # .args[0])
    if SHOWTRACE:
        print(f"Type: {exc_type}")
        print(f"Traceback: ")
        traceback.print_tb(exc_traceback)

if __name__ == "__main__":
    main()