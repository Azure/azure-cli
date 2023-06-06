# CLI test data folder

This folder contains test data for some AKS CLI commands. 

For HTTP proxy testing, we need a preknown certificate which we will present to AKS
and also inject to a VM for use in a proxy server. We can't generate the certificate 
at VM deploy time because we won't be able to extract it easily to pass back to AKS
without e.g. VM run-command which is slow. So we generate the certificate here and
hardcode the key/cert into a VM provisioning script. 

The existing cert is a self-signed CA with a 10 year expiry (Not After: Mar 5 16:44:47 2032 GMT) with a SAN of the
proxy server hostname.

You can regenerate it with the following openssl commands in bash.

After regenerating it, update the certificate in httpproxyconfig.json used for cluster creation, 
and the hardcoded key/cert in setup_proxy.sh.

The cert in httpproxyconfig_update.json can be generated the same way, but it should not need to be updated.

```bash
# Name of the VM on which proxy is hosted
HOST="cli-proxy-vm"

CONFIG="
[req]
distinguished_name=dn
[ dn ]
[ ext ]
basicConstraints=CA:TRUE,pathlen:0
"

openssl req -config <(echo "$CONFIG") -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes -keyout squidk.pem -out squidc.pem -subj "/CN=${HOST}" -addext "subjectAltName=DNS:${HOST}" -addext "basicConstraints=critical,CA:TRUE,pathlen:0" -addext "keyUsage=critical,keyCertSign,cRLSign,keyEncipherment,encipherOnly,decipherOnly,digitalSignature,nonRepudiation" -addext "extendedKeyUsage=clientAuth,serverAuth"

# update cert in testdata file
jq --arg cert "$(cat squidc.pem | base64 -w 0)" '.trustedCa=$cert' httpproxyconfig.json | sponge httpproxyconfig.json
```
