# Stop on error
$ErrorActionPreference = "Stop"

# Đường dẫn project
$APP_DIR = "..\firebase_version\Run_system_app"
$CERT_DIR = Join-Path $APP_DIR "certs"
$KEY_FILE = Join-Path $CERT_DIR "server-key.pem"
$CRT_FILE = Join-Path $CERT_DIR "server.pem"
$CONF_FILE = Join-Path $CERT_DIR "openssl.cnf"

# Lấy IP LAN hiện tại
$IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } | Select-Object -First 1).IPAddress
$HOSTNAME = $env:COMPUTERNAME

# Tạo thư mục cert nếu chưa tồn tại
if (-Not (Test-Path $CERT_DIR)) { New-Item -ItemType Directory -Path $CERT_DIR | Out-Null }

# Tạo file openssl.cnf
@"
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
"@ | Out-File -Encoding ascii $CONF_FILE

Write-Host "[*] Generating SSL cert for IP: $IP"
$OpenSSL = "C:\Program Files\OpenSSL-Win64\bin\openssl.exe"

# Chạy openssl (cần cài OpenSSL trên Windows và thêm vào PATH)
& "$OpenSSL" req -x509 -nodes -days 365 `
    -newkey rsa:2048 `
    -keyout $KEY_FILE `
    -out $CRT_FILE `
    -config $CONF_FILE

Write-Host "[+] Cert generated: $CRT_FILE (IP=$IP)`n"
Write-Host "👉 Truy cập ứng dụng tại:"
Write-Host "   https://$IP:5000"
Write-Host "   https://$HOSTNAME.local:5000 (nếu mDNS hoạt động)`n"

# Chuyển thư mục app
Set-Location $APP_DIR

Write-Host "[*] Starting Flask app on $IP:5000 ..."
python app.py
