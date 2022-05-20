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
import inspect

try:
    # Import the generated grpc source files
    this_dir = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.join(this_dir, "generated"))

    import hbbft_service_pb2
    import hbbft_service_pb2_grpc

except ImportError:
    raise Exception(
        "Protobuf files must be generated from .proto files by the protobuf generator. "
        "Use the included 'generate_protobuf_sources' script to complete this."
    )

from node_ip_data import node_ip_lut


class BackendServiceSender(threading.Thread):
    """
    This class sends backend service grpc messages to the destination machine
    """

    def __init__(self, node_id):

        # Daemon allow thread to close upon application close
        super().__init__(daemon=True)

        # Queue object to store the messages to send
        self.sender_queue = None
        self.node_id = node_id
        self.remote_host_closed = threading.Event()

    def get_sender_queue(self):
        """
        Get the message queue into which the messages to send are being pushed

        :return Queue object of the queue
        """
        return self.sender_queue

    def register_sender_queue(self, queue):
        """
        Register the message queue into which the messages to send are being pushed

        :return Queue object of the queue
        """
        self.sender_queue = queue

        return self.sender_queue

    def run(self):
        """
        This is the main loop of the backend service sender thread
        """
        if self.sender_queue == None:
            print("BackendServiceSender: sender queue unavailble. Exiting")
            return

        empty_exception = None
        # gevent.queue.Queue class has no __module__ attribute
        # so we need to test the type of sender queue differently here
        if "gevent" in str(type(self.sender_queue)):
            from gevent.queue import Empty

            empty_exception = Empty
        else:
            empty_exception = inspect.getmodule(self.sender_queue).Empty

        while True:
            # Check the sender queue and send the message (if any)
            try:
                # Use timeout here to make the thread interruptable with KeyboardInterrupt
                # msg_to_send has format (dest, (round_id, dest, header, msg))
                (dest_node_id, broadcast_msg) = self.sender_queue.get_nowait()
                print(f"Node: {self.node_id} calling a BroadcastCall to node {dest_node_id}")
                # Lookup the destination IP address
                if dest_node_id in node_ip_lut:
                    dest_ip = node_ip_lut[dest_node_id]["ip_addr"]
                    dest_port = node_ip_lut[dest_node_id]["port"]
                    with grpc.insecure_channel(f"{dest_ip}:{dest_port}") as channel:
                        stub = hbbft_service_pb2_grpc.BackendServiceStub(channel)
                        # Send request over gRPC
                        stub.BroadcastCall(broadcast_msg)
                else:
                    print(
                        f"Node {self.node_id}: Unable to find the IP address of dest_node_id={dest_node_id}"
                    )
            except empty_exception:
                # Handle empty queue exception here
                pass
            time.sleep(0)
