#!/usr/bin/env bash

set -xe

# TODO: see if this is necessary?
# disables automatic updates
systemctl disable --now apt-daily{,-upgrade}.{timer,service}

# wait for any unattended upgrades to finish
echo "Waiting for unattended upgrades to finish..."
systemd-run --property="After=apt-daily.service apt-daily-upgrade.service" --wait /bin/true

echo "Removing Canonical snapd"
apt purge snapd -y
