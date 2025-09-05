#!/bin/bash
chmod +x SmartMed.sh
set -e

APP_DIR="/home/deluca/Project/IOT_2025/IOT_challenge_RIO/firebase_version"
CERT_DIR="$APP_DIR/certs"
KEY_FILE="$CERT_DIR/server-key.pem"
CRT_FILE="$CERT_DIR/server.pem"
CONF_FILE="$CERT_DIR/openssl.cnf"

# Lấy IP LAN hiện tại
IP=$(hostname -I | awk '{print $1}')
HOSTNAME=$(hostname)

mkdir -p "$CERT_DIR"

cat > "$CONF_FILE" <<EOF
[req]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = dn
x509_extensions    = v3_req

[dn]
CN = $HOSTNAME

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1   = $HOSTNAME
DNS.2   = $HOSTNAME.local
DNS.3   = localhost
IP.1    = 127.0.0.1
IP.2    = $IP
EOF

echo "[*] Generating SSL cert for IP: $IP"

openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CRT_FILE" \
    -config "$CONF_FILE" >/dev/null 2>&1

echo "[+] Cert generated: $CRT_FILE (IP=$IP)"
echo ""
echo "👉 Truy cập ứng dụng tại:"
echo "   https://$IP:5000"
echo "   https://$HOSTNAME.local:5000 (nếu mDNS hoạt động)"
echo ""

cd "$APP_DIR"

echo "[*] Starting Flask app on $IP:5000 ..."
python app_raspi.py
