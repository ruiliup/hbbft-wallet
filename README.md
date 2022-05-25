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
3. To run docker-compose
```
docker-compose up
```

Manual steps to install hbbft.
1. under root, run `pip install -r requirements.txt`.
2. in grpc_tool, run `python generate_protobuf_sources.py`.
3. under root, run `python setup.py install`.
4. go to hbbft-wallet/hbbft/server/HoneyBadgerBFT-Python, run `python setup.py install`.

Manual steps to run test.
1. go to test, run `python test_user_service_server.py`.
2. go to test, run `python test_user_service_client.py`.