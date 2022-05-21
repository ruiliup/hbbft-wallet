from concurrent import futures
import logging
import grpc

from hbbft.common.protos import hbbft_service_pb2, hbbft_service_pb2_grpc


class BackendService(hbbft_service_pb2_grpc.BackendServiceServicer):
    def BroadcastCall(self, request, context):
        print("BroadcastCall received")
        print(request)
        # Decode the message and push it to honeybadger core queue
        sender = request.src_node_id
        rd = request.round_id
        msg = request.payload
        return hbbft_service_pb2.google_dot_protobuf_dot_empty__pb2.Empty()


def start_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hbbft_service_pb2_grpc.add_BackendServiceServicer_to_server(
        BackendService(), server
    )
    server.add_insecure_port("[::]:50050")
    server.start()
    print("Service started")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    start_server()
    print("Service ended")
