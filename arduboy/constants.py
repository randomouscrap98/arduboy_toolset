
FLASHSIZE = 32768         # Size of the onboard flash (default chip whatever, atmega etc)

FX_PAGESIZE = 256       # The hardware page size in the FX modchip flash
FX_BLOCKSIZE = 65536    # The hardware block size in the FX etc
FX_PAGES_PER_BLOCK = FX_BLOCKSIZE // FX_PAGESIZE 
