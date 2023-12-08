#!/bin/sh
# This script is meant to run "correctly" regardless if it's the first time
# or sometime later. You can of course modify this script to do whatever you
# need, it does waste quite a lot of time with pip installs

# Set these if you need
LPYTHON=python3
LPIP=pip
VENVDIR=.venv


# Create the virtual environment if it doesn't exist
if [ ! -d "$VENVDIR" ]
then
    $LPYTHON -m venv "$VENVDIR"
    echo "Created virtual environment $VENVDIR"
fi

# Enter the virtual environment
source "$VENVDIR/bin/activate"

# Restore the requirements every time. Yes this is wasteful
$PIP install -r requirements.txt

# Run the program
$LPYTHON main_gui.py

# Exit the virtual environment (probably not necessary)
deactivate