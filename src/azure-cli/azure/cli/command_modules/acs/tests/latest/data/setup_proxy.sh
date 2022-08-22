#!/usr/bin/env bash
set -x

echo "setting up"
WORKDIR="${1:-$(mktemp -d)}"
echo "setting up ${WORKDIR}"

pushd "$WORKDIR"

apt update -y && apt install -y apt-transport-https curl gnupg make gcc < /dev/null

# add diladele apt key
wget -qO - https://packages.diladele.com/diladele_pub.asc | apt-key add -

# add new repo
tee /etc/apt/sources.list.d/squid413-ubuntu20.diladele.com.list <<EOF
deb https://squid413-ubuntu20.diladele.com/ubuntu/ focal main
EOF

# and install
apt-get update && apt-get install -y squid-common squid-openssl squidclient libecap3 libecap3-dev < /dev/null

mkdir -p /var/lib/squid

/usr/lib/squid/security_file_certgen -c -s /var/lib/squid/ssl_db -M 4MB || true

chown -R proxy:proxy /var/lib/squid

# Name of the VM on which Squid is hosted
HOST="cli-proxy-vm"

tee squidc.pem > /dev/null <<EOF
-----BEGIN CERTIFICATE-----
MIIFGzCCAwOgAwIBAgIUOQoj8CLZdselr97rvIwx5OLDsuwwDQYJKoZIhvcNAQEL
BQAwFzEVMBMGA1UEAwwMY2xpLXByb3h5LXZtMB4XDTIyMDMwODE2NDQ0N1oXDTMy
MDMwNTE2NDQ0N1owFzEVMBMGA1UEAwwMY2xpLXByb3h5LXZtMIICIjANBgkqhkiG
9w0BAQEFAAOCAg8AMIICCgKCAgEA/MPtV5BTPt6cqi4RdMlmr3yIsa2ujzchxv4h
jsC1DtnRgos5S41PH0ri+3tTSVX32yrwsY+rD1YRupm6lmE7GhU5I0Gi9ozkSF0Z
KKaJi2oypU/FB+QPqzoCRsMEwGCbmKFVl8VuhyndXK4b4kblr9bl/euwd7M8Sbvz
WUjneDrQsiIsrzPT4KAZLqctzDe4llPT7YKa33hiEPOfvWiZ+dqkaQA9P64xXSyn
fHX8uVAJ3uBVJeGxD0pkNJ7jOryaUuHHucU8S9mIjnKjAB5aPjLH5xAs6lmb3122
y+1tnEAmXM50D+UoEjfS6HOb5rdiqXGvc1KboKjzkPCRxx2a72cvegUj6mgAJLzg
ThE1llcmU4izgxoIMkVpGTVOLLn1VFKuNhMZCvFvKgnKoAv3G0FUnfWEaRRjSNmD
LYaMDT5H9Zt2pDIUjUGStCl7gRzMEnYwJO3yiDpg43o5dRysUyL9JfE/Nh7Tg618
n8cJ/W7+QYbYljurap8r7QFSrol3VChFB+Oor5ni+vohSAwJf0UlMpG3xWmy1UI4
TFKfFGRRTzrP+7bNwX5hIvIy5VtgyaOqJwTxhi/JdxtOr2tA5rCW7+CtgSvzkqNE
Xyr7vkYgp6Y5LZgy4tUjK0K0OUgVdjBOhDpEzy/FF8w1FEVgJ0qY/rWcLkBHDT8R
vJkhio8CAwEAAaNfMF0wFwYDVR0RBBAwDoIMY2xpLXByb3h5LXZtMBIGA1UdEwEB
/wQIMAYBAf8CAQAwDwYDVR0PAQH/BAUDAwfngDAdBgNVHSUEFjAUBggrBgEFBQcD
AgYIKwYBBQUHAwEwDQYJKoZIhvcNAQELBQADggIBAAomjCyXvaQOxgYK50sXLB2+
wAfdsx5nnGdgyfg4urW2Vm15DhGvI7C/ntq0dYy24N/UbG7UDXvlyLIJFq1XP7nf
pZG0VCjZ69bmxKm3Z8m0/AwMvi8e9edy8v9kNBCwLGkHbA8Yo9CIiQgelfpp1vUh
bnNBhaD+iu6CfiCLwgJb/iw7eo/CyoZqx+tjXaO2zXvm4p/+QIfAOgtGQLFU8cfZ
/gUrTq5gFq0+P9GyWsATJF6q7L6WZZj0OuTse7f4CSij6MnOMMxA+JoahJz7lsSi
TJHIwEp5r/RyhpyepQxFYcUH5JJf9rahXLWZi+9TjxSM2YyhxfRPsiUEuGDok78Q
m/QPiCi9JJb1ocmTjAV8xDShocivXOFyhn6Ln77vLjY+AavtWDhQthpuPxsLtVzm
e0SH11dELRtb74mqXOrO7fu/+IBs3JqLE/U+xuxQtvG8vG1yDKHHSZqS2h/Ws4l4
NiAshHgehQDPBcY9wYYzfBgZpOUMzdDf50x+FSlY43WOJJzSuQh4yZ0+3kyguCF8
rnMLSceyS4ci4LmJ/KCSuGdf6XVYz8BE9gjjjpCP6qy0UlRefWs/ig/wcK+2bF1T
n/Yv+6gXeCTHJ75qDIPlp7DRUUk0fbMj4bIkaogWWk4zf2u8mxZLa0lePKNKZN/m
GCvFwr3ei+u/8czp5F7T
-----END CERTIFICATE-----
EOF

tee squidk.pem > /dev/null <<EOF
-----BEGIN PRIVATE KEY-----
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
07oi7EDdo42CbbjAFVk2H40iMvVR5d4U
-----END PRIVATE KEY-----
EOF

chown proxy:proxy squidc.pem
chown proxy:proxy squidk.pem
chmod 400 squidc.pem 
chmod 400 squidk.pem
cp squidc.pem /etc/squid/squidc.pem
cp squidk.pem /etc/squid/squidk.pem
cp squidc.pem /usr/local/share/ca-certificates/squidc.crt
update-ca-certificates 

sed -i 's~http_access deny all~http_access allow all~' /etc/squid/squid.conf
sed -i "s~http_port 3128~http_port $HOST:3128\nhttps_port $HOST:3129 tls-cert=/etc/squid/squidc.pem tls-key=/etc/squid/squidk.pem~" /etc/squid/squid.conf

systemctl restart squid
systemctl status squid

# validation, fails VM creation if commands fail
curl -fsSl -o /dev/null -w '%{http_code}\n' -x http://${HOST}:3128/ -I http://www.google.com
curl -fsSl -o /dev/null -w '%{http_code}\n' -x http://${HOST}:3128/ -I https://www.google.com
curl -fsSl -o /dev/null -w '%{http_code}\n' -x https://${HOST}:3129/ -I http://www.google.com
curl -fsSl -o /dev/null -w '%{http_code}\n' -x https://${HOST}:3129/ -I https://www.google.com
