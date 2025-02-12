#!/bin/sh
# This script is meant to run "correctly" regardless if it's the first time
# or sometime later. You can of course modify this script to do whatever you
# need, it does waste quite a lot of time with pip installs
set -e

# Set these if you need
LPYTHON=python3
LPIP=pip3
VENVDIR=.venv

# Create the virtual environment if it doesn't exist
if [ ! -d "$VENVDIR" ]; then
	echo "Creating virtual environment $VENVDIR"
	$LPYTHON -m venv "$VENVDIR"
fi

# Enter the virtual environment
echo "Entering virtual environment $VENVDIR"
. "$VENVDIR/bin/activate"

# Restore the requirements every time. Yes this is wasteful
echo "Installing requirements"
$LPIP install -r requirements.txt

# Run the program
echo "Running program"
$LPYTHON main_gui.py

# Exit the virtual environment (probably not necessary)
deactivate

