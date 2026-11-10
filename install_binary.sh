#!/usr/bin/env bash
# Taýýar binary-ny Ubuntu-da gurmak (Python gerek däl)
# Ulanylyşy:  bash install_binary.sh
set -e

if [ "$(id -u)" -eq 0 ]; then
    echo "Muny root hökmünde däl, adaty ulanyjy hökmünde işlediň (sudo ýok)."
    exit 1
fi

HERE="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/.local/share/usb_suzgic"
BIN_DIR="$HOME/.local/bin"

if [ ! -f "$HERE/usb_suzgic" ]; then
    echo "usb_suzgic (binary) faýly bu skript bilen bir papkada bolmaly."
    exit 1
fi

mkdir -p "$APP_DIR" "$BIN_DIR" "$HOME/.config/autostart" "$HOME/.local/share/applications"
cp "$HERE/usb_suzgic" "$APP_DIR/usb_suzgic"
chmod +x "$APP_DIR/usb_suzgic"
ln -sf "$APP_DIR/usb_suzgic" "$BIN_DIR/usb-suzgic"

cat > "$HOME/.local/share/applications/usb-suzgic.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=USB Süzgüç (sazlamalar)
Exec=$APP_DIR/usb_suzgic
Terminal=true
Icon=drive-removable-media-usb
Categories=Utility;
EOF

cat > "$HOME/.config/autostart/usb-suzgic-watch.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=USB Süzgüç (gözegçilik)
Exec=$APP_DIR/usb_suzgic --watch
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo
echo "Gurnaldy!"
echo "Sazlamak üçin:  $APP_DIR/usb_suzgic"
echo "Giňeltmeleri girizdiňizden soň kompýuteri täzeden açyň, gözegçilik özi başlar."
