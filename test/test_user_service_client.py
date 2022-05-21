import grpc
from hbbft.client.user_service_client import UserServiceClient
from hbbft.common.protos import hbbft_service_pb2, hbbft_service_pb2_grpc
from hbbft.common.setting import user_service_port

if __name__ == "__main__":
    client = UserServiceClient(num=2)
    client.create_txns(2)
    client.close()
