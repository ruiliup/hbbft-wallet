# cs244b Final project

## Docker setup (in root directory)

1. build image (choose arbitrary image name):
```
docker build -t [image-name] . 
```
2. run container (use "-v local/directory:container/directory" to mount local directory into container):
```
docker run -v local/path/to/code:container/path/to/code -it [image-name] /bin/bash
```