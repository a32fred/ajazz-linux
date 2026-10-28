Name:           ajazz-linux
Version:        0.1.0
Release:        1%{?dist}
Summary:        Unofficial Linux settings app for the AJAZZ AJ199 mouse
License:        MIT
URL:            https://github.com/a32fred/ajazz-linux
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  systemd-rpm-macros
Requires:       %{name}-cli = %{version}-%{release}
Requires:       python3-pyside6
Recommends:     libnotify

# Dependencies are listed by hand: the wheel metadata names the PyPI Qt package, which would pull
# Qt into the dependency-free cli package and does not match the distribution's python3-pyside6.
%global __pythondist_requires %{nil}

%global _description %{expand:
DPI stages and colors, button assignments, macros and the scroll wheel light for the
AJAZZ AJ199 mouse, with desktop notifications for DPI changes and low battery. Unofficial
and not affiliated with the manufacturer.}

%description %{_description}

This package is the graphical application. The command line tools and the udev rule are
in the %{name}-cli package, which has no GUI dependencies.

%package cli
Summary:        Command line tools and udev rule for the AJAZZ AJ199 mouse
Requires:       python3 >= 3.10

%description cli %{_description}

Scan, status, dump, listen and restore commands that use only the Python standard
library, plus the udev rule that gives the logged-in user access to the mouse.

%prep
%autosetup -n %{name}-%{version}

%generate_buildrequires
%pyproject_buildrequires -R

%build
%pyproject_wheel

%install
%pyproject_install
# The wheel's data files are for pip users; this package installs them explicitly.
rm -rf %{buildroot}%{_datadir}/applications %{buildroot}%{_datadir}/icons %{buildroot}%{_datadir}/doc
# Only ajazz-linux is installed system-wide; "vela" is a generic name other software uses.
rm -f %{buildroot}%{_bindir}/vela
install -Dpm 0644 packaging/linux/io.github.a32fred.ajazz_linux.metainfo.xml %{buildroot}%{_metainfodir}/io.github.a32fred.ajazz_linux.metainfo.xml
install -Dpm 0644 packaging/linux/70-ajazz-linux.rules %{buildroot}%{_udevrulesdir}/70-ajazz-linux.rules
install -Dpm 0644 packaging/linux/ajazz-linux.desktop %{buildroot}%{_datadir}/applications/ajazz-linux.desktop
install -Dpm 0644 packaging/linux/ajazz-linux.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/ajazz-linux.svg

%post cli
# Apply the rule to a mouse that is already plugged in, so no replug is needed.
udevadm control --reload-rules >/dev/null 2>&1 || :
udevadm trigger --subsystem-match=hidraw --action=add >/dev/null 2>&1 || :

%files cli
%license LICENSE THIRD_PARTY_NOTICES.md
%doc README.md
%{python3_sitelib}/vela/
%exclude %{python3_sitelib}/vela/ui/
%exclude %{python3_sitelib}/vela/assets/
%{python3_sitelib}/ajazz_linux-%{version}.dist-info/
%{_bindir}/ajazz-linux
%{_udevrulesdir}/70-ajazz-linux.rules

%files
%{python3_sitelib}/vela/ui/
%{python3_sitelib}/vela/assets/
%{_datadir}/applications/ajazz-linux.desktop
%{_metainfodir}/io.github.a32fred.ajazz_linux.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/ajazz-linux.svg

%changelog
* Wed Oct 28 2026 a32fred <fredericocarlos.a32@gmail.com> - 0.1.0-1
- First package: split into a dependency-free CLI and the Qt application.
