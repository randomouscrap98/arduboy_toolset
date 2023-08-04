
# Pad data to a multiple of the given size. For instance, if data is 245 but multsize is
# 256, it is padded up to 256 with the given pad data. If data is 400 and multsize is 256,
# it is padded up to 512
def pad_data(data, multsize, pad = b'\xFF'):
    if len(data) % multsize: 
        data += pad * (multsize - (len(data) % multsize))
    return data