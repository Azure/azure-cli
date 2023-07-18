$baseImages = @("ubuntu:xenial", "ubuntu:bionic", "debian:stretch","debian:jessie", "debian:buster")

foreach ($image in $baseImages) {
    docker build --build-arg base=${image} -t deb-installer:current -f Dockerfile.install_test .
    $result = $LastExitCode
    if ($result -ne 0) {
        exit $result
    }
    docker run -it --rm deb-installer:current
    $result = $LastExitCode
    if ($result -ne 0) {
        exit $result
    }
}