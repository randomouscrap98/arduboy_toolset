
import os

VERSION = "0.7.0"
SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))

IMAGE_FILEFILTER = "Images (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)"
HEX_FILEFILTER = "All Supported Files (*.hex);;All Files (*)"
BIN_FILEFILTER = "All Supported Files (*.bin);;All Files (*)"
ARDUHEX_FILEFILTER = "All Supported Files (*.hex *.arduboy *.zip);;All Files (*)"
ARDUBOY_FILEFILTER = "All Supported Files (*.arduboy);;All Files (*)"
HEADER_FILEFILTER = "All Supported Files (*.h);;All Files(*)"

TINYFONT = "m3x6.ttf"
TINYFONT_WIDTH = 4 #WARN: This is not always the case!!

# These constants should maybe come from a config file
OFFICIAL_BASE_URL = "http://www.bloggingadeadhorse.com/cart/"
OFFICIAL_CARTMETA_URL = OFFICIAL_BASE_URL + "Cart_GetBINs.php"
OFFICIAL_CARTDATE_URL = OFFICIAL_BASE_URL + "Cart_LastModification.php"
OFFICIAL_INDEX = OFFICIAL_BASE_URL + "Cart.html"