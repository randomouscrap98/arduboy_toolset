# set -e

# Stuff you may want to change
NAME="arduboy_toolset"
PUBLISHDIR="publish"
EXTRAS="config.toml"
# NOTE: INSTALLEXTRAS is something expected to be set by a parent script

# Everything published is release now, since we can use musl
BUILDTARGETS="x86_64-unknown-linux-gnu x86_64-pc-windows-gnu"
BUILDTYPE="release"

# We clear out the publish folder (always fresh) and recreate it
echo "Prepping $PUBLISHDIR"
rm -rf "$PUBLISHDIR"
mkdir -p "$PUBLISHDIR"

for target in $BUILDTARGETS
do
   # Before we do anything, we need to install the musl target. It may 
   # already be installed
   echo "Installing rust target for linux"
   rustup target add ${target}

   # Now, we build for the target.
   BUILDPARAM="--release --target=${target}"
   echo "Building $target"
   cargo build ${BUILDPARAM}

   PUBLISHEND="$PUBLISHDIR/$target"
   mkdir -p $PUBLISHEND
   cp -r $EXTRAS "$PUBLISHEND"
   cp "target/${target}/${BUILDTYPE}/${NAME}" "$PUBLISHEND"
   cp "target/${target}/${BUILDTYPE}/${NAME}.exe" "$PUBLISHEND"
done

echo "All done!"
