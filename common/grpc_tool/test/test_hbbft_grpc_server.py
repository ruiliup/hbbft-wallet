import time
from concurrent import futures
import logging
import os
import sys
import grpc
from queue import Queue

try:
    # Import the generated pb files
    test_script_path = os.path.dirname(os.path.realpath(__file__))
    grpc_tool_path = os.path.dirname(test_script_path)
    sys.path.append(os.path.join(grpc_tool_path, "generated"))

    import user_service_pb2
    import user_service_pb2_grpc
    import hbbft_service_pb2
    import hbbft_service_pb2_grpc

except ImportError:
    raise Exception(
        "Protobuf files must be generated from .proto files by the protobuf generator. "
        "Use the included 'generate_protobuf_sources' script to complete this."
    )

from test_user_data import account_data

database = Queue()


class UserService(user_service_pb2_grpc.UserServiceServicer):
    def GetBalanceCall(self, request, context):
        print(f"GetBalance service requested for {request.account_id}")
        if (
            request.account_id in account_data
            and account_data[request.account_id]["user_name"] == request.user_name
        ):
            return user_service_pb2.GetBalanceResponse(
                account_id=request.account_id,
                timestamp_ms=(1000000000 + request.account_id),
                balance=account_data[request.account_id]["balance"],
            )

    def PayToCall(self, request, context):
        print("PayTo service requested")
        if (
                request.src_account_id in account_data
                and account_data[request.src_account_id]["user_name"]
                == request.src_user_name
                and request.des_account_id in account_data
                and account_data[request.des_account_id]["user_name"]
                == request.des_user_name
        ):
            print(
                f"Paying from accound_id={request.src_account_id}, balance={account_data[request.src_account_id]['balance']}, to accound_id={request.des_account_id}, balance={account_data[request.des_account_id]['balance']}"
            )
            account_data[request.src_account_id]["balance"] -= request.amount
            account_data[request.des_account_id]["balance"] += request.amount
            print(
                f"Paid from accound_id={request.src_account_id}, balance={account_data[request.src_account_id]['balance']}, to accound_id={request.des_account_id}, balance={account_data[request.des_account_id]['balance']}"
            )
            txn = user_service_pb2.PayToRequest(
                src_account_id=request.src_account_id,
                src_user_name=request.src_user_name,
                des_account_id=request.des_account_id,
                des_user_name=request.des_user_name,
                amount=request.amount,
                timestamp=time.time()
            )
            database.put(txn)
            return user_service_pb2.GetBalanceResponse(
                account_id=request.src_account_id,
                timestamp_ms=(1000000000 + request.src_account_id),
                balance=account_data[request.src_account_id]["balance"],
            )


class HBBFTService(hbbft_service_pb2_grpc.HBBFTServiceServicer):
    """Missing associated documentation comment in .proto file."""

    def GetTransactions(self, request, context):
        """Missing associated documentation comment in .proto file."""
        while not database.empty():
            txn = database.get()
            yield txn


def run():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    hbbft_service_pb2_grpc.add_HBBFTServiceServicer_to_server(HBBFTService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Service started")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    run()
