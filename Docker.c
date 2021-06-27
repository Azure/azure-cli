$ docker run -u ''$'(id -u):''$'(id -g) -v 
''$'{HOME}:/home/az -e HOME=/home/az --rm -it mcr.microsoft.com/azure-cli:<version>
