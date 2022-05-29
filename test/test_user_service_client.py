import grpc
from hbbft.client.user_service_client import UserServiceClient
from hbbft.common.protos import hbbft_service_pb2, hbbft_service_pb2_grpc
from hbbft.common.setting import user_service_port

import time

if __name__ == "__main__":
    time.sleep(3)
    client = UserServiceClient(ip="172.16.238.2", num=2)
    client.create_txns(200)
    client.close()
    client = UserServiceClient(ip="172.16.238.3", num=2)
    client.create_txns(200)
    client.close()
    client = UserServiceClient(ip="172.16.238.4", num=2)
    client.create_txns(200)
    client.close()
    client = UserServiceClient(ip="172.16.238.5", num=2)
    client.create_txns(200)
    client.close()