#!/bin/sh
# Build the .deb files (architecture: all) in a clean Debian container: ./packaging/build-deb.sh
# Output: dist/deb/ajazz-linux-cli_<version>_all.deb and ajazz-linux_<version>_all.deb
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
version=$(sed -n 's/^version = "\(.*\)"/\1/p' "$root/pyproject.toml")
mkdir -p "$root/dist/deb"
podman run --rm -e VERSION="$version" -v "$root:/src:ro,Z" -v "$root/dist/deb:/out:Z" debian:trixie sh -ec '
set -eu
stage=/tmp/stage; rm -rf "$stage"
py=usr/lib/python3/dist-packages
mkdir -p $stage/cli/$py $stage/cli/usr/bin $stage/cli/usr/lib/udev/rules.d $stage/cli/usr/share/doc/ajazz-linux-cli $stage/cli/DEBIAN
mkdir -p $stage/gui/$py/vela $stage/gui/usr/share/applications $stage/gui/usr/share/icons/hicolor/scalable/apps $stage/gui/usr/share/doc/ajazz-linux $stage/gui/DEBIAN
# core: everything except the Qt interface and its assets
cp -r /src/src/vela $stage/cli/$py/vela
rm -rf $stage/cli/$py/vela/ui $stage/cli/$py/vela/assets
cp -r /src/src/vela/ui $stage/gui/$py/vela/ui
cp -r /src/src/vela/assets $stage/gui/$py/vela/assets
find $stage -name __pycache__ -type d -prune -exec rm -rf {} +
for name in ajazz-linux vela; do
  printf "#!/usr/bin/python3\nimport sys\nfrom vela.app import main\nsys.exit(main())\n" > $stage/cli/usr/bin/$name
  chmod 0755 $stage/cli/usr/bin/$name
done
install -m 0644 /src/packaging/linux/70-ajazz-linux.rules $stage/cli/usr/lib/udev/rules.d/
install -m 0644 /src/packaging/linux/ajazz-linux.desktop $stage/gui/usr/share/applications/
install -m 0644 /src/packaging/linux/ajazz-linux.svg $stage/gui/usr/share/icons/hicolor/scalable/apps/
for pkg in cli gui; do
  name=ajazz-linux; [ $pkg = cli ] && name=ajazz-linux-cli
  install -d $stage/$pkg/usr/share/doc/$name
  { echo "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"; echo "Upstream-Name: ajazz-linux";
    echo "Source: https://github.com/a32fred/ajazz-linux"; echo; echo "Files: *"; echo "Copyright: 2026 a32fred and contributors";
    echo "License: MIT"; echo " See /usr/share/common-licenses or the LICENSE file in the source repository."; } > $stage/$pkg/usr/share/doc/$name/copyright
done
install -m 0644 /src/README.md /src/THIRD_PARTY_NOTICES.md $stage/cli/usr/share/doc/ajazz-linux-cli/
cat > $stage/cli/DEBIAN/control <<CTRL
Package: ajazz-linux-cli
Version: $VERSION
Architecture: all
Maintainer: a32fred <fredericocarlos.a32@gmail.com>
Depends: python3 (>= 3.10)
Section: utils
Priority: optional
Homepage: https://github.com/a32fred/ajazz-linux
Description: Command line tools and udev rule for the AJAZZ AJ199 mouse
 Scan, status, dump, listen and restore commands for the AJAZZ AJ199 mouse, using only
 the Python standard library, plus the udev rule that lets the logged-in user open the
 mouse. Unofficial; not affiliated with the manufacturer.
CTRL
cat > $stage/gui/DEBIAN/control <<CTRL
Package: ajazz-linux
Version: $VERSION
Architecture: all
Maintainer: a32fred <fredericocarlos.a32@gmail.com>
Depends: ajazz-linux-cli (= $VERSION), python3-pyside6.qtcore, python3-pyside6.qtgui, python3-pyside6.qtwidgets, python3-pyside6.qtsvg, python3-pyside6.qtsvgwidgets
Section: utils
Priority: optional
Homepage: https://github.com/a32fred/ajazz-linux
Description: Unofficial Linux settings app for the AJAZZ AJ199 mouse
 DPI stages and colors, button assignments, macros and the scroll wheel light, with
 desktop notifications for DPI changes and low battery. Needs the Qt 6 Python bindings,
 which Ubuntu 24.04 does not ship; install with pipx there. Not affiliated with the manufacturer.
CTRL
cat > $stage/cli/DEBIAN/postinst <<SH
#!/bin/sh
set -e
if [ "\$1" = configure ]; then
  # Byte-compile for every installed Python 3 so start-up never compiles in memory.
  if command -v py3compile >/dev/null 2>&1; then py3compile -p ajazz-linux-cli || true; fi
  udevadm control --reload-rules >/dev/null 2>&1 || true
  udevadm trigger --subsystem-match=hidraw --action=add >/dev/null 2>&1 || true
fi
exit 0
SH
cat > $stage/cli/DEBIAN/prerm <<SH
#!/bin/sh
set -e
if command -v py3clean >/dev/null 2>&1; then py3clean -p ajazz-linux-cli || true; fi
exit 0
SH
cat > $stage/gui/DEBIAN/postinst <<SH
#!/bin/sh
set -e
if [ "\$1" = configure ] && command -v py3compile >/dev/null 2>&1; then py3compile -p ajazz-linux || true; fi
exit 0
SH
cat > $stage/gui/DEBIAN/prerm <<SH
#!/bin/sh
set -e
if command -v py3clean >/dev/null 2>&1; then py3clean -p ajazz-linux || true; fi
exit 0
SH
chmod 0755 $stage/*/DEBIAN/postinst $stage/*/DEBIAN/prerm
find $stage -type d -exec chmod 0755 {} +
dpkg-deb --root-owner-group --build $stage/cli /out/ajazz-linux-cli_${VERSION}_all.deb
dpkg-deb --root-owner-group --build $stage/gui /out/ajazz-linux_${VERSION}_all.deb
'
ls -la "$root/dist/deb"
