import datetime
import os
import sys
import pathlib
import socket
import threading
import time
from queue import Queue

from concurrent import futures
import logging
import grpc

try:
    # Import the generated grpc source files
    this_dir = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.dirname(this_dir)
    sys.path.append(parent_dir)
    sys.path.append(os.path.join(parent_dir, "generated"))

    import hbbft_service_pb2

    from backend_service_receiver import BackendServiceReceiver
    from backend_service_sender import BackendServiceSender

except ImportError:
    raise Exception(
        "Failed to import the BackendServiceReceiver and BackendServiceSender classes"
    )


NUM_OF_NODES = 4


def run_test():
    receiver_classes = {}
    receiver_queues = {}
    sender_classes = {}
    sender_queues = {}
    # Instantiate the receiver classes for each node
    for node_id in range(NUM_OF_NODES):
        receiver_classes[node_id] = BackendServiceReceiver(node_id)
        receiver_queues[node_id] = receiver_classes[node_id].register_receiver_queue(
            Queue()
        )
    # Instantiate the sender classes for each node
    for node_id in range(NUM_OF_NODES):
        sender_classes[node_id] = BackendServiceSender(node_id)
        sender_queues[node_id] = sender_classes[node_id].register_sender_queue(Queue())

    # Start all the sender/receiver threads for each node
    for node_id in range(NUM_OF_NODES):
        receiver_classes[node_id].start()
        sender_classes[node_id].start()

    # Test sending messages
    print("--------- Test send message to self --------")
    for test_itr in range(5):
        for node_id in range(NUM_OF_NODES):
            bcast_msg = hbbft_service_pb2.BroadcastMessage(
                src_node_id=node_id, msg_id=0, round_id=0, op_type='ACS_ABA'
            )
            sender_queues[node_id].put((node_id, bcast_msg))
            time.sleep(0.1)
    print("--------- Test broadcast message --------")
    for test_itr in range(5):
        for src_node_id in range(NUM_OF_NODES):
            for dest_node_id in range(NUM_OF_NODES):
                bcast_msg = hbbft_service_pb2.BroadcastMessage(
                    src_node_id=src_node_id, msg_id=0, round_id=0, op_type='ACS_ABA'
                )
                sender_queues[node_id].put((dest_node_id, bcast_msg))
                time.sleep(0.1)
    # Join all the sender/receiver threads for each node
    for node_id in range(NUM_OF_NODES):
        sender_classes[node_id].join()
        receiver_classes[node_id].join()


if __name__ == "__main__":
    logging.basicConfig()
    run_test()
