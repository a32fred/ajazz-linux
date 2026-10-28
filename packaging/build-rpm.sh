#!/bin/sh
# Build the RPMs in a clean Fedora container: ./packaging/build-rpm.sh [fedora-version] (default 44)
# Output: dist/rpm/*.rpm
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
version=$(sed -n 's/^version = "\(.*\)"/\1/p' "$root/pyproject.toml")
fedora=${1:-44}
mkdir -p "$root/dist/rpm"
tarball=$(mktemp -d)/ajazz-linux-$version.tar.gz
# Working tree minus build and VCS directories, so local changes are what gets packaged.
tar -C "$root" --transform "s,^\./,ajazz-linux-$version/," --exclude=./.git --exclude=./.venv --exclude=./dist \
    --exclude='*.egg-info' --exclude=__pycache__ -czf "$tarball" .
podman run --rm -v "$tarball:/src.tar.gz:ro,Z" -v "$root/dist/rpm:/out:Z" -v "$root/packaging/rpm/ajazz-linux.spec:/ajazz-linux.spec:ro,Z" \
    "fedora:$fedora" sh -ec '
  dnf -y -q install rpm-build python3-devel pyproject-rpm-macros systemd-rpm-macros python3-setuptools python3-pip python3-wheel >/dev/null
  mkdir -p /root/rpmbuild/SOURCES /root/rpmbuild/SPECS
  cp /src.tar.gz /root/rpmbuild/SOURCES/ajazz-linux-'"$version"'.tar.gz
  cp /ajazz-linux.spec /root/rpmbuild/SPECS/
  rpmbuild -ba /root/rpmbuild/SPECS/ajazz-linux.spec
  cp /root/rpmbuild/RPMS/noarch/*.rpm /root/rpmbuild/SRPMS/*.rpm /out/
'
ls -la "$root/dist/rpm"
