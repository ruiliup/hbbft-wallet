import logging
import os
import sys
import grpc

try:
    # Import the generated pb files
    test_script_path = os.path.dirname(os.path.realpath(__file__))
    grpc_tool_path = os.path.dirname(test_script_path)
    sys.path.append(os.path.join(grpc_tool_path, "generated"))

    import user_service_pb2
    import user_service_pb2_grpc

except ImportError:
    raise Exception(
        "Protobuf files must be generated from .proto files by the protobuf generator. "
        "Use the included 'generate_protobuf_sources' script to complete this."
    )

from test_user_data import account_data


# Test the get balance service request
def user_get_balance(stub):
    for aid in account_data:
        uname = account_data[aid]["user_name"]
        print(f"Getting account balance for accound_id={aid}, user_name={uname}")
        # Send request over gRPC
        response = stub.GetBalanceCall(
            user_service_pb2.GetBalanceRequest(account_id=aid)
        )
        # Check response
        if response is None:
            print("Failed to get balance")
        elif response.balance == account_data[aid]["balance"]:
            print(f"Successfully get balance={response.balance}")
        else:
            print(f"Balance does not match.")
            print(f"We got {response.balance} from blockchain, and we want {account_data[aid]['balance']}")


def user_pay_to(stub):
    pay_amount = 10
    # Select two users
    aid_a = list(account_data.keys())[0]
    aid_b = list(account_data.keys())[1]
    uname_a = account_data[aid_a]["user_name"]
    uname_b = account_data[aid_b]["user_name"]
    print(
        f"Paying from accound_id={aid_a}, user_name={uname_a} to accound_id={aid_b}, user_name={uname_b}"
    )
    # Send get balance request over gRPC
    response = stub.GetBalanceCall(
        user_service_pb2.GetBalanceRequest(account_id=aid_a, user_name=uname_a)
    )
    bal_a = response.balance
    response = stub.GetBalanceCall(
        user_service_pb2.GetBalanceRequest(account_id=aid_b, user_name=uname_b)
    )
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
    paid_response = stub.GetBalanceCall(
        user_service_pb2.GetBalanceRequest(account_id=aid_b, user_name=uname_b)
    )
    # Check the result
    if ((bal_a - response.balance) == pay_amount) and (
        (paid_response.balance - bal_b) == pay_amount
    ):
        print(f"Successfully paid ={pay_amount}")
    else:
        print(f"Failed to pay, {response.balance}, {paid_response.balance}")


def run():

    with grpc.insecure_channel("localhost:50051") as channel:
        stub = user_service_pb2_grpc.UserServiceStub(channel)
        print("-------- Test GetBalance --------")
        user_get_balance(stub)
        print("-------- Test PayTo --------")
        user_pay_to(stub)


if __name__ == "__main__":
    logging.basicConfig()
    run()
