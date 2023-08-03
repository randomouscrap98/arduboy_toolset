# Arduboy toolset (not official)

I just wanted to learn about Arduboy by making some of the existing tools.
There are better tools to use (such as
https://github.com/MrBlinky/Arduboy-Python-Utilities). I recommend using those
instead.

## What tools?

I plan on having:
- A .hex and .arduboy flasher
- A bin flasher for the FX memory
- Something to save and restore the eeprom
- Something to save/restore the flash and fx mem
- A cart builder (using all local files in a custom format, not the existing .csv format)
- perhaps a way to "reverse engineer" an existing bin file so it is easier to simply "add" games to an existing cart
  (depends on complexity)

## Releases

I hope to have releases built for at least windows and linux. I assume building for macOS is possible but I don't know
if I can cross-compile that (probably not). Releases will come in the future.

## Building

### Linux prerequirements

You'll need (only if building from source!):
- **Rust**, get it from https://rustup.rs/
- **libudev**, available as `libudev-dev` on debian-based systems (Ubuntu)
- **libxcb** (or portions of it), available as `libxcb-render0-dev libxcb-shape0-dev libxcb-xfixes0-dev` on deb etc
- **libssl**, available as `libssl-dev` deb etc
- **libxkbcommon**, available as `libxkbcommon-dev` deb etc
- **libspeechd** available as `libspeechd-dev` deb etc
- **pkg-config**, available as `pkg-config` deb etc

### Windows prerequirements

You'll need:
- **Rust**, get it from https://rustup.rs/
- **Mingw**, get it from https://www.mingw-w64.org/ (TODO: actually test this)
- **The mingw rust target**, `rustup target add x86_64-pc-windows-gnu`
- ??? (will add later)

### Running / Building

Running is the same on all systems:

```sh
cd arduboy_toolset
cargo run
```

Or if you want to create an executable and reuse it without rust (linux shown, change x86-64-etc with appropriate runtime):

```sh
cd arduboy_toolset
cargo build --release
cp target/x86-64-unknown-linux-gnu/release/arduboy_toolset .
./arduboy_toolset
```

Note that the "config.toml" file is needed wherever you plan on running the executable.

### Publishing 

The "publish.sh" script will attempt to build all the possible cross-compilation stuff (assumed to be running on
linux ofc). It will require quite a few things, and is mostly made for me:

- **All the linux prereqs** (see above)
- **mingw-w64** (called as such on Debian based systems)


## Caveats
- I can't seem to build purely statically linked (using musl). I may have to build for glibc, or have people build from source.
  - This is apparently normal: they say specifically that the glibc version links against the external library libudev, and not
    including that (which I assume is removed for the static linked musl build)
- If I can't get the windows build to recognize the arduboy then this project is dead in the water utnil I figure that out

