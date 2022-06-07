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
4. To open a client, open a container with `--network=hbbft-wallet_app_net` after `docker-compose up`, and run `python test/test_user_service_client_demo.py`

Manual steps to install hbbft.
1. under root, run `pip install -r requirements.txt`.
2. in grpc_tool, run `python generate_protobuf_sources.py`.
3. under root, run `python setup.py install`.
4. go to hbbft-wallet/hbbft/server/HoneyBadgerBFT-Python, run `python setup.py install`.

Manual steps to run test.
1. go to test, run `python test_user_service_server.py`.
2. go to test, run `python test_user_service_client.py`.

## AWS setup

1. on each node, start a docker container using our Dockerfile that exposes port 50050 and 50051.
2. open a shell in the container, run `python grpc_tool/generate_protobuf_sources.py`
3. run `./run.sh N f pid B` where N is number of nodes, f is number of failure nodes tolerated, pid is node id for node, B is batch size. This command needs to be executed almost simultaneous on all nodes.
4. Our default configuration is N = 4, f = 1. If you wish to run more than N nodes, change the ip addresses in hbbft/common/setting.py, and change the thsigN_t.keys and thencN_t.keys files in run.sh to, say, thsig8_2.keys and thenc8_2.keys. These are generated with `python -m honeybadgerbft.crypto.threshsig.generate_keys N (f+1)` and `python -m honeybadgerbft.crypto.threshenc.generate_keys N (N-2*f)` respectively