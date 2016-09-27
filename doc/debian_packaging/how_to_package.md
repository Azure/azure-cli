Packaging the CLI as a Debian package
=====================================

Create a new VM to use for packaging (e.g. Ubuntu 14.04)

```
sudo apt-get update
```

Install latest versions of pip and virtualenv:
```
sudo apt-get install -y curl
curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
sudo python get-pip.py
sudo pip install virtualenvwrapper
```

Install dh-virtualenv by building from GitHub repo:
```
sudo apt-get install -y devscripts git equivs
git clone https://github.com/spotify/dh-virtualenv.git
cd dh-virtualenv
sudo mk-build-deps -ri
```

Modify dh-virtualenv/debian/control to not include the python-virtualenv dependencies as we don't use python-virtualenv but use the ones above instead.
```
nano debian/control
```

Build dh-virtualenv:
```
dpkg-buildpackage -us -uc -b
sudo dpkg -i ../dh-virtualenv_<version>_all.deb 
```

Install dependencies for the build:
```
sudo apt-get install -y libssl-dev libffi-dev python-dev
```

The directory name should match the package version you wish to release:
```
cp -r ~/azure-cli ~/azure-cli-<version>
cd ~/azure-cli-<version>; dpkg-buildpackage -us -uc
```

Now you have built the package, you can install it directly with the following.
Alternatively, upload the package to an apt repository.
```
sudo dpkg -i ~/azure-cli_<version>_all.deb
```
