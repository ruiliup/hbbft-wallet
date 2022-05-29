from concurrent import futures
import grpc
from queue import Queue
from hbbft.common.protos import user_service_pb2, user_service_pb2_grpc
from hbbft.common.protos import hbbft_service_pb2, hbbft_service_pb2_grpc

database = Queue()


class UserService(user_service_pb2_grpc.UserServiceServicer):
    def PayToCall(self, request, context):
        # print("PayTo service requested")
        try:
            txn = user_service_pb2.PayToRequest(
                src_acct=request.src_acct,
                des_acct=request.des_acct,
                amount=request.amount,
                timestamp=request.timestamp
            )
            database.put(txn)

        except grpc.RpcError as e:
            print(e)
            return user_service_pb2.PayToResponse(status=False)
        else:
            return user_service_pb2.PayToResponse(status=True)


class HBBFTService(hbbft_service_pb2_grpc.HBBFTServiceServicer):
    """Missing associated documentation comment in .proto file."""

    def GetTransactions(self, request, context):
        """Missing associated documentation comment in .proto file."""
        while not database.empty():
            txn = database.get()
            yield txn


class UserServiceServer(object):
    def __init__(self, port: int = 50051):
        self.port = port

    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        user_service_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
        hbbft_service_pb2_grpc.add_HBBFTServiceServicer_to_server(HBBFTService(), server)
        server.add_insecure_port(f"[::]:{self.port}")
        server.start()
        print("User Service Server started", flush=True)
        server.wait_for_termination()
