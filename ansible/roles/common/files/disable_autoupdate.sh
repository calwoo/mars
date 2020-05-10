#!/usr/bin/env bash

set -xe

# log all user data invocations to console:
# from https://aws.amazon.com/premiumsupport/knowledge-center/ec2-linux-log-user-data/
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# TODO: see if this is necessary?
# disables automatic updates
echo "Disabling automatic updates..."
sudo systemctl disable --now apt-daily{,-upgrade}.{timer,service}

# wait for any unattended upgrades to finish
echo "Waiting for unattended upgrades to finish..."
sudo systemd-run --property="After=apt-daily.service apt-daily-upgrade.service" --wait /bin/true