#!/usr/bin/env bash

RASPBIAN_BASE=${1:-"/media/$USER/boot"}
echo "Setting up raspbian boot partition at $RASPBIAN_BASE"
SSID=${2:-"$(nmcli -t dev wifi list | cut -d ':' -f2)"}

read -e -p "Enter WiFi password for $SSID" PSK
(( ${#PSK} < 8 )) && echo "The password is too short" && exit 1


cat <<EOF > "$RASPBIAN_BASE/wpa_supplicant.conf"
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={
	ssid="${SSID}"
	psk="${PSK}"
	key_mgmt=WPA-PSK
}
EOF

read -p "Enable SSH y/n ?" SSH
[ "${SSH:0:1}" == "y" ] && echo > "$RASPBIAN_BASE/ssh"

