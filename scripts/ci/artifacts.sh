# Build wheel and set the $share_folder to the artifacts folder

. $(cd $(dirname $0); pwd)/build.sh
share_folder=$(cd $(dirname $0); cd ../../artifacts; pwd)