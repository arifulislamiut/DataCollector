#!/usr/bin/env bash
# setup_hardware.sh
# Create a stable udev symlink for a device so its path doesn't change after reboot
# Usage: sudo ./setup_hardware.sh /dev/ttyUSB0 input-device [-g dialout] [-m 0660] [-f 99-input-device.rules] [--dry-run]

set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
  echo "This script must be run as root. Use sudo." >&2
  exit 1
fi

if [[ "${1:-}" == "" || "${2:-}" == "" ]]; then
  echo "Usage: sudo $0 /dev/ttyUSB0 symlink_name [-g group] [-m mode] [-f rule_filename] [--dry-run]" >&2
  exit 1
fi

DEVPATH="$1"
SYMLINK_NAME="$2"
GROUP="dialout"
MODE="0660"
RULE_FILE="99-${SYMLINK_NAME}.rules"
DRY_RUN=0

shift 2
while (($#)); do
  case "$1" in
    -g|--group) GROUP="$2"; shift 2 ;;
    -m|--mode) MODE="$2"; shift 2 ;;
    -f|--file) RULE_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

DEVNAME="$(basename "$DEVPATH")"
if [[ ! -e "/dev/$DEVNAME" ]]; then
  echo "Device /dev/$DEVNAME not found. Plug device in and try again." >&2
  exit 2
fi

UDEV_A="$(udevadm info -a -n "/dev/$DEVNAME" 2>/dev/null || true)"
UDEV_PROP="$(udevadm info -q property -n "/dev/$DEVNAME" 2>/dev/null || true)"

extract_attr() {
  local key="$1"
  echo "$UDEV_A" | grep -m1 "ATTRS{$key}" || true
}

SERIAL_LINE="$(extract_attr serial || true)"
SERIAL=""
if [[ -n "$SERIAL_LINE" ]]; then
  SERIAL="$(echo "$SERIAL_LINE" | sed -E 's/.*ATTRS\{serial\}=="([^"]+)".*/\1/')"
fi
if [[ -z "$SERIAL" ]]; then
  SERIAL="$(echo "$UDEV_PROP" | awk -F= '/^ID_SERIAL_SHORT=/{print $2; exit}')" || true
fi

VID_LINE="$(extract_attr idVendor || true)"
PID_LINE="$(extract_attr idProduct || true)"
VID=""
PID=""
if [[ -n "$VID_LINE" ]]; then
  VID="$(echo "$VID_LINE" | sed -E 's/.*ATTRS\{idVendor\}=="([^"]+)".*/\1/')"
fi
if [[ -n "$PID_LINE" ]]; then
  PID="$(echo "$PID_LINE" | sed -E 's/.*ATTRS\{idProduct\}=="([^"]+)".*/\1/')"
fi

RULE=""
if [[ -n "$SERIAL" ]]; then
  RULE="SUBSYSTEM==\"tty\", ATTRS{serial}==\"${SERIAL}\", MODE=\"${MODE}\", GROUP=\"${GROUP}\", SYMLINK+=\"${SYMLINK_NAME}\""
elif [[ -n "$VID" && -n "$PID" ]]; then
  RULE="SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"${VID}\", ATTRS{idProduct}==\"${PID}\", MODE=\"${MODE}\", GROUP=\"${GROUP}\", SYMLINK+=\"${SYMLINK_NAME}\""
else
  echo "Could not determine serial or vendor/product for /dev/$DEVNAME." >&2
  echo "Dumping udev info:" >&2
  echo "-------------------------------------------------" >&2
  echo "$UDEV_A" >&2
  exit 3
fi

RULE_PATH="/etc/udev/rules.d/${RULE_FILE}"

echo "Will create udev rule: $RULE_PATH"
echo "Rule contents:"
echo "$RULE"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run; not writing file."
  exit 0
fi

if [[ -f "$RULE_PATH" ]]; then
  cp -a "$RULE_PATH" "${RULE_PATH}.bak"
  echo "Backed up existing rule to ${RULE_PATH}.bak"
fi

cat > "/tmp/${RULE_FILE}" <<EOF
# udev rule created by setup_hardware.sh
# device: /dev/${DEVNAME}
# generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
$RULE
EOF

mv "/tmp/${RULE_FILE}" "$RULE_PATH"
chmod 644 "$RULE_PATH"

udevadm control --reload-rules
udevadm trigger --action=add

sleep 0.2

echo
if [[ -e "/dev/${SYMLINK_NAME}" ]]; then
  ls -l "/dev/${SYMLINK_NAME}"
else
  echo "/dev/${SYMLINK_NAME} not present yet. Try unplug/replug the device or run:" >&2
  echo "  sudo udevadm trigger --action=add" >&2
fi

echo
echo "Installed rule: $RULE_PATH"

echo "To replicate on another machine, copy this script and run with sudo:" 
echo "  sudo ./setup_hardware.sh /dev/ttyUSB0 input-device -g dialout -m 0660"
