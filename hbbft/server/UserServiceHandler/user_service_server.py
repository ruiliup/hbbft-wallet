import datetime
import time
from concurrent import futures
import grpc
import os
from queue import Queue
from hbbft.common.protos import user_service_pb2, user_service_pb2_grpc
from honeybadgerbft.core.honeybadger import HoneyBadgerBFT
from hbbft.common.setting import total_server, block_path_header, server_id

database = Queue()


class UserService(user_service_pb2_grpc.UserServiceServicer):
    def PayToCall(self, request, context):
        # print("PayTo service requested", flush=True)
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
        now = datetime.datetime.now()
        end = now + datetime.timedelta(minutes=5)
        while now <= end:
            # for server_id in range(total_server):
            block_path = f'{block_path_header}{server_id}'
            if os.path.exists(block_path):
                acct = HoneyBadgerBFT.get_balance(block_path, request.account_id)
                return user_service_pb2.GetBalanceResponse(account=acct)
            time.sleep(5)
            now = datetime.datetime.now()
        print("Blocks not found after 5 min", flush=True)
        return None

    def GetAccountsCall(self, request, context):
        # since each node has same files we pick up node 0 here
        now = datetime.datetime.now()
        end = now + datetime.timedelta(minutes=5)
        while now <= end:
            # for server_id in range(total_server):
            block_path = f'{block_path_header}{server_id}'
            # print("block path: ", block_path, flush=True)
            if os.path.exists(block_path):
                accts = HoneyBadgerBFT.get_accounts(
                    block_path)  # a list of Accounts
                response = user_service_pb2.GetAccountsResponse()
                print(response)
                for acct in accts:
                    response.accounts.append(acct)
                return response
            else:
                response = user_service_pb2.GetAccountsResponse()
                return response
            time.sleep(5)
            now = datetime.datetime.now()
        print("Blocks not found after 5 min", flush=True)
        return None

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
            # print(f'register: {usr_txn}', flush=True)

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
