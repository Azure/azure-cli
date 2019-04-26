$baseImages = @("ubuntu:xenial", "ubuntu:bionic", "debian:stretch","debian:jessie")

foreach ($image in $baseImages) {
    docker build --build-arg base=${image} -t deb-installer:current -f Dockerfile.install_test .
    $result = $LastExitState
    if ($result -ne 0) {
        exit $result
    }
    docker run -it --rm deb-installer:current
    $result = $LastExitState
    if ($result -ne 0) {
        exit $result
    }
}