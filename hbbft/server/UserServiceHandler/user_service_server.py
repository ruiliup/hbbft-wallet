import time
from concurrent import futures
import grpc
import os
from queue import Queue
from hbbft.common.protos import user_service_pb2, user_service_pb2_grpc
from honeybadgerbft.core.honeybadger import HoneyBadgerBFT

database = Queue()


class UserService(user_service_pb2_grpc.UserServiceServicer):
    def PayToCall(self, request, context):
        print("PayTo service requested", flush=True)
        try:
            txn = user_service_pb2.PayToRequest(
                src_acct=request.src_acct,
                des_acct=request.des_acct,
                amount=request.amount,
                timestamp=request.timestamp
            )
            user_txn = user_service_pb2.UserTransaction()
            user_txn.transaction.CopyFrom(txn)
            database.put(user_txn)

        except grpc.RpcError as e:
            print(e, flush=True)
            return user_service_pb2.PayToResponse(status=False)
        else:
            return user_service_pb2.PayToResponse(status=True)

    def GetBalanceCall(self, request, context):
        # since each node has same files, we pick up node 0 here.
        block_path = f'/usr/local/src/hbbft-wallet/test/blocks/block_file_0'
        while not os.path.exists(block_path):
            time.sleep(5)
            print("Blocks not found. Wait 5 sec...", flush=True)
        acct = HoneyBadgerBFT.get_balance(block_path, request.account_id)
        return user_service_pb2.GetBalanceResponse(account=acct)

    def Register(self, request, context):
        try:
            account = user_service_pb2.Account(
                account_id=request.account_id,
                user_name=request.user_name,
                balance=request.balance
            )
            usr_txn = user_service_pb2.UserTransaction()
            usr_txn.account.CopyFrom(account)
            database.put(usr_txn)
            print(f'register: {usr_txn}', flush=True)

        except grpc.RpcError as e:
            print(e, flush=True)
            return user_service_pb2.RegisterResponse(status=False)
        else:
            return user_service_pb2.RegisterResponse(status=True)

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
        server.add_insecure_port(f"[::]:{self.port}")
        server.start()
        print("User Service Server started", flush=True)
        server.wait_for_termination()
