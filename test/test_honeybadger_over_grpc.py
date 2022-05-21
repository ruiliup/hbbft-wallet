import gevent
from gevent.event import Event
from gevent.queue import Queue, Empty
from pytest import fixture, mark, raises
from gevent import monkey

monkey.patch_all(thread=False)

from hbbft.server.BackendServiceHandler.backend_service_receiver import BackendServiceReceiver
from hbbft.server.BackendServiceHandler.backend_service_sender import BackendServiceSender
from hbbft.common.protos import hbbft_service_pb2


import honeybadgerbft.core.honeybadger
from honeybadgerbft.core.honeybadger import HoneyBadgerBFT
from honeybadgerbft.crypto.threshsig.boldyreva import (
    dealer,
    serialize,
    deserialize1,
)
from honeybadgerbft.crypto.threshenc import tpke
from honeybadgerbft.core.honeybadger import BroadcastTag


@fixture
def recv_queues(request):
    from honeybadgerbft.core.honeybadger import BroadcastReceiverQueues

    number_of_nodes = getattr(request, "N", 4)
    queues = {
        tag.value: [Queue() for _ in range(number_of_nodes)]
        for tag in BroadcastTag
        if tag != BroadcastTag.TPKE
    }
    queues[BroadcastTag.TPKE.value] = Queue()
    return BroadcastReceiverQueues(**queues)


from pytest import mark

import inspect
import time
import pickle

grpc_receiver_classes = []
grpc_receiver_queues = []
grpc_sender_classes = []
grpc_sender_queues = []


def grpc_router(N):
    """Builds a set of gRPC sender/receiver for each node

    :return: (receives, sends)
    """
    grpc_receiver_classes = [BackendServiceReceiver(node_id) for node_id in range(N)]
    grpc_receiver_queues = [Queue() for _ in range(N)]
    grpc_sender_classes = [BackendServiceSender(node_id) for node_id in range(N)]
    grpc_sender_queues = [Queue() for _ in range(N)]

    def makeSend(i):
        print(f"Setting up grpc sender for node {i}")
        # Register the sender queue of each node and start the services
        grpc_sender_classes[i].register_sender_queue(grpc_sender_queues[i])
        grpc_sender_classes[i].start()

        def _send(j, o):
            # serialize message
            round_id = o[0]
            op_msg = o[1]
            # op_msg of format ('Header', dest_id, payload)
            op_type = op_msg[0]
            op_id = op_msg[1]
            op_payload = op_msg[2]
            bcast_msg = hbbft_service_pb2.BroadcastMessage(
                src_node_id=i, msg_id=op_id, round_id=round_id, op_type=op_type
            )
            if "ACS_COIN" == op_type:
                bcast_msg.cc_op.tag = op_payload[0]
                bcast_msg.cc_op.round = op_payload[1]
                bcast_msg.cc_op.ser_sig = serialize(op_payload[2])
            elif "TPKE" == op_type:
                for share in op_payload:
                    bcast_msg.te_op.ser_shares.append(tpke.serialize(share))
            elif "ACS_RBC" == op_type:
                bcast_msg.rb_op.payload = pickle.dumps(op_payload)
            elif "ACS_ABA" == op_type:
                bcast_msg.ba_op.payload = pickle.dumps(op_payload)
            else:
                print(f"Unknown message type {o}")

            # Push the message (j, o) to the gRPC sender queue of node i
            grpc_sender_queues[i].put((j, bcast_msg))
            # print(f"Send round {round_id}: [{i} -> {j}]")

        return _send

    def makeRecv(j):
        print(f"Setting up grpc receiver for node {j}")
        # Register the receiver queue of each node and start the services
        grpc_receiver_classes[j].register_receiver_queue(grpc_receiver_queues[j])
        grpc_receiver_classes[j].start()

        def _recv():
            # Get the message (src_id, o) from the gRPC receiver queue of node j
            while True:
                try:
                    bcast_msg = grpc_receiver_queues[j].get_nowait()
                    src_id = bcast_msg.src_node_id
                    round_id = bcast_msg.round_id
                    op_type = bcast_msg.op_type
                    msg_id = bcast_msg.msg_id
                    op_msg = getattr(bcast_msg, bcast_msg.WhichOneof("operation"))

                    # Deserialize message payload
                    des_op_msg = None
                    if "ACS_COIN" == op_type:
                        des_op_msg = (
                            op_msg.tag,
                            op_msg.round,
                            deserialize1(op_msg.ser_sig),
                        )
                    elif "TPKE" == op_type:
                        # print('TPKE message recv')
                        des_op_msg = []
                        for share in op_msg.ser_shares:
                            des_op_msg.append(tpke.deserialize1(share))
                    elif "ACS_RBC" == op_type:
                        des_op_msg = pickle.loads(op_msg.payload)
                    elif "ACS_ABA" == op_type:
                        des_op_msg = pickle.loads(op_msg.payload)
                    else:
                        print(f"Unknown message type {o}")

                    # message o has format (round_id, ('Header', dest_id, payload))
                    o = (round_id, (op_type, msg_id, des_op_msg))
                    # print(f"Recv round {o[0]}: [{src_id} -> {j}]")
                    return (src_id, o)
                except Empty:
                    time.sleep(0)

        return _recv

    return ([makeSend(i) for i in range(N)], [makeRecv(j) for j in range(N)])


# Test asynchronous common subset
def _test_honeybadger(N=4, f=1, seed=None):
    sid = "sidA"
    # Generate threshold sig keys
    sPK, sSKs = dealer(N, f + 1, seed=seed)
    # Generate threshold enc keys
    ePK, eSKs = tpke.dealer(N, f + 1)

    sends, recvs = grpc_router(N)
    time.sleep(1)

    badgers = [None] * N
    threads = [None] * N
    for i in range(N):
        badgers[i] = HoneyBadgerBFT(
            sid, i, 1, N, f, sPK, sSKs[i], ePK, eSKs[i], sends[i], recvs[i]
        )
        threads[i] = gevent.spawn(badgers[i].run)

    for i in range(N):
        # if i == 1: continue
        badgers[i].submit_tx("<[HBBFT Input %d]>" % i)

    for i in range(N):
        badgers[i].submit_tx("<[HBBFT Input %d]>" % (i + 10))

    for i in range(N):
        badgers[i].submit_tx("<[HBBFT Input %d]>" % (i + 20))

    # gevent.killall(threads[N-f:])
    # gevent.sleep(3)
    # for i in range(N-f, N):
    #    inputs[i].put(0)
    try:
        outs = [threads[i].get() for i in range(N)]
        # gevent.joinall(threads)
        # Consistency check
        assert len(set(outs)) == 1

    except KeyboardInterrupt:
        gevent.killall(threads)
        raise


# @mark.skip('python 3 problem with gevent')
# def test_honeybadger():
if __name__ == "__main__":
    _test_honeybadger()


@mark.parametrize("message", ("broadcast message",))
@mark.parametrize("node_id", range(4))
@mark.parametrize("tag", [e.value for e in BroadcastTag])
@mark.parametrize("sender", range(4))
def test_broadcast_receiver_loop(sender, tag, node_id, message, recv_queues):
    from honeybadgerbft.core.honeybadger import broadcast_receiver_loop

    recv = Queue()
    recv.put((sender, (tag, node_id, message)))
    gevent.spawn(broadcast_receiver_loop, recv.get, recv_queues)
    recv_queue = getattr(recv_queues, tag)
    if tag != BroadcastTag.TPKE.value:
        recv_queue = recv_queue[node_id]
    assert recv_queue.get() == (sender, message)


@mark.parametrize("message", ("broadcast message",))
@mark.parametrize("node_id", range(4))
@mark.parametrize("tag", ("BogusTag", None, 123))
@mark.parametrize("sender", range(4))
def test_broadcast_receiver_loop_raises(sender, tag, node_id, message, recv_queues):
    from honeybadgerbft.core.honeybadger import broadcast_receiver_loop
    from honeybadgerbft.exceptions import UnknownTagError

    recv = Queue()
    recv.put((sender, (tag, node_id, message)))
    with raises(UnknownTagError) as exc:
        broadcast_receiver_loop(recv.get, recv_queues)
    expected_err_msg = "Unknown tag: {}! Must be one of {}.".format(
        tag, BroadcastTag.__members__.keys()
    )
    assert exc.value.args[0] == expected_err_msg
    recv_queues_dict = recv_queues._asdict()
    tpke_queue = recv_queues_dict.pop(BroadcastTag.TPKE.value)
    assert tpke_queue.empty()
    assert all([q.empty() for queues in recv_queues_dict.values() for q in queues])
