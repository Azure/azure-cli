# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# vmss application health setting for rolling upgrade policy

application_health_setting_for_linux = '''
#cloud-config
package_upgrade: true

packages:
  - nginx

write_files:
  - path: /var/www/html/index.html
    content: |
      <!DOCTYPE html>
      <html>
      <body>
      <h1>Hello, World!</h1>
      </body>
      </html>
    owner: www-data:www-data
    permissions: '0644'
  - path: /var/www/html/health.html
    content: |
      healthy
    owner: www-data:www-data
    permissions: '0644'
  - path: /etc/nginx/sites-available/default
    content: |
      server {
          listen 80 default_server;
          listen [::]:80 default_server;
          root /var/www/html;
          index index.html;
          server_name _;
          location / {
              try_files $uri $uri/ =404;
          }
          location /health {
              try_files $uri.html =404;
          }
      }
    owner: root:root
    permissions: '0644'

runcmd:
  - systemctl enable nginx
  - service nginx restart
'''

application_health_setting_for_windows = '''
#!/bin/bash

apt-get update -y && apt-get upgrade -y
apt-get install -y nginx
echo "Hello World from host" $HOSTNAME "!" | sudo tee -a /var/www/html/index.html
'''
