import logging
import sys
import gui
import cli
import traceback


# Main entry point!
def main():

    global SHOWTRACE

    # Some initial setup
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    print("", flush=True)

if __name__ == "__main__":
    sys.excepthook = custom_excepthook
    main()