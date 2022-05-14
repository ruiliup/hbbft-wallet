import grpc
from hbbft.client.user_service_client import UserServiceClient
from hbbft.common.grpc_tool.generated import hbbft_service_pb2, hbbft_service_pb2_grpc
from hbbft.common.setting import user_service_port

if __name__ == "__main__":
    client = UserServiceClient(num=2)
    client.create_txns(2)
    client.close()
    # test get transactions from grpc.
    with grpc.insecure_channel(f'localhost:{user_service_port}') as channel:
        # fetch this txn from grpc to hbbft.
        stub2 = hbbft_service_pb2_grpc.HBBFTServiceStub(channel)
        request = hbbft_service_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
        txns = stub2.GetTransactions(request)
        for t in txns:
            print(t)
