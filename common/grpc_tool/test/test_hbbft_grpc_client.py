"""
Honeybadger has recv function to receive transactions from external.
We implement function here to feed this recv so Honeybadger can process those transactions.
"""
import grpc
import os
import sys
from test_user_data import account_data

try:
    # Import the generated pb files
    test_script_path = os.path.dirname(os.path.realpath(__file__))
    grpc_tool_path = os.path.dirname(test_script_path)
    sys.path.append(os.path.join(grpc_tool_path, "generated"))

    import hbbft_service_pb2
    import hbbft_service_pb2_grpc
    import user_service_pb2
    import user_service_pb2_grpc

except ImportError:
    raise Exception(
        "Protobuf files must be generated from .proto files by the protobuf generator. "
        "Use the included 'generate_protobuf_sources' script to complete this."
    )


def user_pay_to(stub):
    pay_amount = 10
    # Select two users
    aid_a = list(account_data.keys())[0]
    aid_b = list(account_data.keys())[1]
    uname_a = account_data[aid_a]["user_name"]
    uname_b = account_data[aid_b]["user_name"]
    print(f"Paying from accound_id={aid_a}, user_name={uname_a} to accound_id={aid_b}, user_name={uname_b}")
    # Send get balance request over gRPC
    response = stub.GetBalanceCall(
        user_service_pb2.GetBalanceRequest(account_id=aid_a, user_name=uname_a)
    )
    bal_a = response.balance
    response = stub.GetBalanceCall(user_service_pb2.GetBalanceRequest(account_id=aid_b, user_name=uname_b))
    bal_b = response.balance
    response = stub.PayToCall(
        user_service_pb2.PayToRequest(
            src_account_id=aid_a,
            src_user_name=uname_a,
            des_account_id=aid_b,
            des_user_name=uname_b,
            amount=pay_amount,
        )
    )
    paid_response = stub.GetBalanceCall(user_service_pb2.GetBalanceRequest(account_id=aid_b, user_name=uname_b))
    # Check the result
    if ((bal_a - response.balance) == pay_amount) and ((paid_response.balance - bal_b) == pay_amount):
        print(f"Successfully paid ={pay_amount}")
    else:
        print(f"Failed to pay, {response.balance}, {paid_response.balance}")


if __name__ == "__main__":
    with grpc.insecure_channel('localhost:50051') as channel:
        # generate txn and send this txn to grpc.
        stub1 = user_service_pb2_grpc.UserServiceStub(channel)
        user_pay_to(stub1)
        # fetch this txn from grpc to hbbft.
        stub2 = hbbft_service_pb2_grpc.HBBFTServiceStub(channel)
        request = hbbft_service_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
        txns = stub2.GetTransactions(request)
        for t in txns:
            print(t)
