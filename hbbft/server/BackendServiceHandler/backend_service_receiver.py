import datetime
import os
import sys
import pathlib
import socket
import threading
import time

from concurrent import futures
import logging
import grpc

from hbbft.common.protos import hbbft_service_pb2, hbbft_service_pb2_grpc


from hbbft.common.setting import node_ip_lut

BACKEND_SERVICE_SERVER_LISTENING_IP = "[::]"


class BackendServiceReceiver(threading.Thread):
    """
    This class receives backend service grpc messages from the source machine, interprets it
    as the proper message type, and places it in the appropriate queue to be read by the backend applications
    """

    def __init__(self, node_id, ip_addrs=BACKEND_SERVICE_SERVER_LISTENING_IP):

        # Daemon allow thread to close upon application close
        super().__init__(daemon=True)

        # Queue object to store the received messages and notify consumer tasks
        self.receiver_queue = None
        if node_id not in node_ip_lut:
            raise ValueError(
                "Invalide node ID: registere node IP in the node_ip_lut table"
            )
        self.node_id = node_id
        self.port = node_ip_lut[node_id]["port"]
        self.listen_to_ip = ip_addrs
        self.remote_host_closed = threading.Event()

    def get_receiver_queue(self):
        """
        Get the message queue into which the received messages are pushed

        :return Queue object of the queue
        """
        return self.receiver_queue

    def register_receiver_queue(self, queue):
        """
        Register the message queue into which the received messages are pushed

        :return Queue object of the queue
        """
        self.receiver_queue = queue

        return self.receiver_queue

    def run(self):
        """
        This is the main loop of the backend service receiver thread
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        hbbft_service_pb2_grpc.add_BackendServiceServicer_to_server(self.create_backend_servicer(), server)
        server.add_insecure_port(f"{self.listen_to_ip}:{self.port}")
        server.start()
        print("Service started")
        server.wait_for_termination()

    def create_backend_servicer(self):
        return self.BackendService(self)

    class BackendService(hbbft_service_pb2_grpc.BackendServiceServicer):
        """
        Inner class which contains all the backend service calls

        :return Queue object of the queue
        """

        def __init__(self, outer_self):
            self.outer_self = outer_self

        def BroadcastCall(self, request, context):
            # print(f"Node: {self.outer_self.node_id} received a BroadcastCall from node {request.src_node_id}")
            # Decode the message and push it to honeybadger core queue
            if self.outer_self.receiver_queue != None:
                self.outer_self.receiver_queue.put(request)
            return hbbft_service_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
