#!/bin/bash
if [ $EUID != 0 ]; then
     sudo bash "$0"
     exit $?
fi
echo ""
echo "Microsoft Azure VM Backup - File Recovery"
echo "______________________________________________"
case `uname` in
Linux)
if [ -f /etc/oracle-release ] && [ -f /etc/redhat-release ] ; then
    if grep -q 'Oracle Linux Server release 6.*' /etc/oracle-release; then
        OS="Oracle;6;"
    elif grep -q 'Oracle Linux Server release 7.*' /etc/oracle-release; then
        OS="Oracle;7;"
    fi
elif [ -f /etc/redhat-release ]; then
    if grep -q 'Red Hat Enterprise Linux Server release 6.*' /etc/redhat-release ; then
        OS="RHEL;6;"
    elif grep -q 'CentOS Linux release 6.*' /etc/redhat-release || \
        grep -q 'CentOS release 6.*' /etc/redhat-release; then
        OS="CentOS;6;"
    elif grep -q 'Red Hat Enterprise Linux Server release 7.* (Maipo)' /etc/redhat-release ; then
        OS="RHEL;7;"
    elif grep -q 'CentOS Linux release 7.* (Core)' /etc/redhat-release ; then
        OS="CentOS;7;"
    fi
elif [ -f /etc/lsb-release ] ; then
    if grep -q 'Ubuntu 12.*' /etc/lsb-release ; then
        OS="Ubuntu;12;"
    elif grep -q 'DISTRIB_RELEASE=14.*' /etc/lsb-release ; then
        OS="Ubuntu;14;"
    elif grep -q 'DISTRIB_RELEASE=16.*' /etc/lsb-release ; then
            OS="Ubuntu;16;"
    fi
elif [ -f /etc/debian_version ]; then
    if grep -q '7.*' /etc/debian_version; then
        OS="Debian;7;"
    elif grep -q '8.*' /etc/debian_version; then
        OS="Debian;8;"
    fi
fi
;;
esac
if [ -z "$OS" ]; then
    echo "This script can be run on a machine with below operation systems."
    echo "Ubuntu 12.04, 14.04, 16.04"
    echo "CentOS 6.5, 6.7, 7.0, 7.1, 7.2"
    echo "RHEL 6.7, 7.2"
    echo "Debian 7, 8"
    echo "Oracle Linux 6.4, 7.0"
    exit
fi
if which python > /dev/null 2>&1;
then
    haspython=$true
else 
    echo "The script requires 'Python' to run. Please install 'Python (2.6.6)' and then run this script again."
    exit
fi
haslshw=0
hasiscsiadm=0
if which iscsiadm > /dev/null 2>&1;
then
    hasiscsiadm=1
else
    hasiscsiadm=0
fi 
if which lshw > /dev/null 2>&1;
then
    haslshw=1
else
    haslshw=0
fi 
MinPort=5365
MaxPort=5396
VMName="iaasvmcontainerv2;pstestrg;clilinuxvm1"
MachineName="clilinuxvm1"
TargetPortalAddress="pod01-rec2.wus.backup.windowsazure.com"
TargetPortalPortNumber=3260
TargetNodeAddress="iqn.2016-01.microsoft.azure.backup:2288626066870276951-711326-52777210750193-84757440223908.636402852922573001"
TargetUserName="2288626066870276951-d3445eac-ba4f-49b1-ab03-5c4093aa4d28"
TargetPassword="19f65783906d43a"
InitiatorChapPassword="2c1fb84e97d649"
ScriptId="c3702a79-710c-4d0a-b67c-42a29799959d"
scriptdirectory="$(cd "$(dirname "$0")"; pwd)"
newguid=$(python -c 'import time; print str(time.strftime("%Y%m%d%H%M%S"))')
logfolder="${scriptdirectory}/${MachineName}-${newguid}"
scriptfolder="${logfolder}/Scripts"
mkdir "${logfolder}"
setfacl --set="user::rwx,group::rwx,other::---" "${logfolder}"
setfacl --default --set="user::rwx,group::rwx,other::---" "${logfolder}"
mkdir "${scriptfolder}"
logfilename="${scriptfolder}/MicrosoftAzureBackupILRLogFile.log"
echo "Setting ACL to Log Folder" > $logfilename
MABILRConfigFolder="/etc/MicrosoftAzureBackupILR"
echo "Setting ACL succeeded"  >> $logfilename
if [ ! -d "${MABILRConfigFolder}" ]
then
    mkdir "${MABILRConfigFolder}" &>> $logfilename
fi
if which wget > /dev/null 2>&1;
then
  echo "using wget for downloading scripts" >> $logfilename
  wget -o "${scriptfolder}/downloadpythonscript1.log" -O "${scriptfolder}/ILRPythonScript.py" "http://download.microsoft.com/download/0/B/F/0BFE2679-CDAB-44FB-8688-54F9FE65F702/ILRPythonScript.py" --secure-protocol=TLSv1 -t 3
  wget -o "${scriptfolder}/downloadpythonscript2.log" -O "${scriptfolder}/SecureTCPTunnel.py" "http://download.microsoft.com/download/0/B/F/0BFE2679-CDAB-44FB-8688-54F9FE65F702/SecureTCPTunnel.py" --secure-protocol=TLSv1 -t 3
else
echo "using curl for downloading scripts" >> $logfilename
  curl --stderr "${scriptfolder}/downloadpythonscript1.log" --url "http://download.microsoft.com/download/0/B/F/0BFE2679-CDAB-44FB-8688-54F9FE65F702/ILRPythonScript.py" --tlsv1.2 --retry 3 > "${scriptfolder}/ILRPythonScript.py"
  curl --stderr "${scriptfolder}/downloadpythonscript2.log" --url "http://download.microsoft.com/download/0/B/F/0BFE2679-CDAB-44FB-8688-54F9FE65F702/SecureTCPTunnel.py" --tlsv1.2 --retry 3 > "${scriptfolder}/SecureTCPTunnel.py"
fi 
# cp "/home/ILRPythonScript.py" "${scriptfolder}/ILRPythonScript.py"
# cp "/home/SecureTCPTunnel.py" "${scriptfolder}/SecureTCPTunnel.py"
if [[ (! -f "${scriptfolder}/ILRPythonScript.py") || (! -f "${scriptfolder}/SecureTCPTunnel.py") ]] 
then
  echo "Unable to access the recovery point. Please make sure that you have enabled access to Azure public IP addresses on the outbound port 3260 and 'https://download.microsoft.com/'"
  exit
fi
python "${scriptfolder}/ILRPythonScript.py" "${OS}" $hasiscsiadm $haslshw "${logfolder}" $ScriptId $MinPort $MaxPort $TargetPortalAddress $TargetPortalPortNumber $TargetNodeAddress $TargetUserName $TargetPassword $VMName $MachineName $InitiatorChapPassword "$1"