import logging
import os
import sys
import grpc

try:
    # Import the generated grpc source files
    this_dir = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.dirname(this_dir)
    sys.path.append(parent_dir)
    sys.path.append(os.path.join(parent_dir, "generated"))

    import hbbft_service_pb2
    import hbbft_service_pb2_grpc

except ImportError:
    raise Exception(
        "Protobuf files must be generated from .proto files by the protobuf generator. "
        "Use the included 'generate_protobuf_sources' script to complete this."
    )

from node_ip_data import node_ip_lut


# Send the backend broadcast message
def backend_send(src_node_id, dest_node_id, rnd, msg):
    print(
        f"Sending message with src_node_id={src_node_id}, dest_node_id={dest_node_id}, round_id={rnd}, payload={msg}"
    )
    # Lookup the destination IP address
    if src_node_id in node_ip_lut:
        dest_ip = node_ip_lut[src_node_id]["ip_addr"]
        with grpc.insecure_channel(f"{dest_ip}:50050") as channel:
            stub = hbbft_service_pb2_grpc.BackendServiceStub(channel)
            # Send request over gRPC
            stub.BroadcastCall(
                hbbft_service_pb2.BroadcastMessage(
                    src_node_id=src_node_id, round_id=rnd, payload=msg
                )
            )


def test_client():
    print("-------- Test Broadcast --------")
    for i in range(50):
        print(f"iteration {i}")
        backend_send(0, 1, i, "test_message")


if __name__ == "__main__":
    logging.basicConfig()
    test_client()
