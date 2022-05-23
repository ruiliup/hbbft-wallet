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

# reload(honeybadgerbft.core.honeybadger)
from honeybadgerbft.core.honeybadger import HoneyBadgerBFT
from honeybadgerbft.crypto.threshsig import boldyreva
from honeybadgerbft.crypto.threshenc import tpke
from honeybadgerbft.core.honeybadger import BroadcastTag
# from honeybadgerbft.core.utils import initiateThresholdSig, initiateThresholdEnc, initiateECDSAKeys, getKeys
from honeybadgerbft.crypto.threshsig.boldyreva_gipc import initialize as initializeGIPC
from honeybadgerbft.crypto.threshenc.tpke import serialize, deserialize0, deserialize1, deserialize2, TPKEPublicKey, TPKEPrivateKey, group

import time
import threading
import pickle
import argparse


def read_keys():
    # read keys from file
    spk_file = open("keys/sPK", "rb")
    sPK_ser = pickle.load(spk_file)
    spk_file.close()
    print(sPK_ser)
    epk_file = open("keys/ePK", "rb")
    ePK_ser = pickle.load(epk_file)
    epk_file.close()

    ssk_file = open("keys/sSK" + str(pid), "rb")
    sSK_ser = pickle.load(ssk_file)
    ssk_file.close()

    esk_file = open("keys/eSK" + str(pid), "rb")
    eSK_ser = pickle.load(esk_file)
    esk_file.close()
    print(len(sPK_ser[3]))
    sPK = boldyreva.TBLSPublicKey(
        sPK_ser[0], 
        sPK_ser[1], 
        boldyreva.deserialize2(sPK_ser[2]),
        [boldyreva.deserialize2(VKp) for VKp in sPK_ser[3]]
    )

    # sSK = boldyreva.TBLSPrivateKey(
    #     sPK_ser[0], 
    #     sPK_ser[1], 
    #     boldyreva.deserialize2(sPK_ser[2]),
    #     [boldyreva.deserialize2(VKp) for VKp in sPK_ser[3]],
    #     boldyreva.deserialize2(sSK_ser[1]),
    #     sSK_ser[0]
    # )

    ePK = tpke.TPKEPublicKey(
        ePK_ser[0], 
        ePK_ser[1], 
        tpke.deserialize2(ePK_ser[2]),
        [tpke.deserialize2(VKp) for VKp in ePK_ser[3]],
    )

    eSK = tpke.TPKEPrivateKey(
        ePK_ser[0], 
        ePK_ser[1], 
        tpke.deserialize2(ePK_ser[2]),
        [tpke.deserialize2(VKp) for VKp in ePK_ser[3]],
        tpke.deserialize2(eSK_ser[1]),
        eSK_ser[0]
    )

    return sPK, sSK, ePK, eSK

def router(pid):
    receiver = BackendServiceReceiver(pid)
    receiver_queue = Queue()
    sender = BackendServiceSender(pid)
    sender_queue = Queue()

    def makeSend(i):
        print("Setting up grpc sender", flush=True)
        sender.register_sender_queue(sender_queue)
        sender.start()
        def _send(j, o):
            # serialize message
            round_id = o[0]
            op_msg = o[1]
            # op_msg of format ('Header', dest_id, payload)
            op_type = op_msg[0]
            op_id = op_msg[1]
            op_payload = op_msg[2]
            bcast_msg = hbbft_service_pb2.BroadcastMessage(src_node_id=i, msg_id=op_id, round_id=round_id, op_type=op_type)
            if 'ACS_COIN' == op_type:
                bcast_msg.cc_op.tag = op_payload[0]
                bcast_msg.cc_op.round = op_payload[1]
                bcast_msg.cc_op.ser_sig = boldyreva.serialize(op_payload[2])
            elif 'TPKE' == op_type:
                # print('TPKE message send')
                # print(op_payload)
                for share in op_payload:
                    bcast_msg.te_op.ser_shares.append(tpke.serialize(share))
            elif 'ACS_RBC' == op_type:
                bcast_msg.rb_op.payload = pickle.dumps(op_payload)
            elif 'ACS_ABA' == op_type:
                bcast_msg.ba_op.payload = pickle.dumps(op_payload)
            else:
                print(f'Unknown message type {o}')

            # Push the message (j, o) to the gRPC sender queue of node i
            sender_queue.put((j, bcast_msg))

        return _send

    def makeRecv():
        print("Setting up grpc receiver", flush=True)
        receiver.register_receiver_queue(receiver_queue)
        receiver.start()

        def _recv():
            while True:
                try:
                    bcast_msg = receiver_queue.get_nowait()
                    src_id = bcast_msg.src_node_id
                    round_id = bcast_msg.round_id
                    op_type = bcast_msg.op_type
                    msg_id = bcast_msg.msg_id
                    op_msg = getattr(bcast_msg, bcast_msg.WhichOneof('operation'))

                    # Deserialize message payload
                    des_op_msg = None
                    if 'ACS_COIN' == op_type:
                        des_op_msg = (op_msg.tag, op_msg.round, boldyreva.deserialize1(op_msg.ser_sig))
                    elif 'TPKE' == op_type:
                        # print('TPKE message recv')
                        des_op_msg = []
                        for share in op_msg.ser_shares:
                            des_op_msg.append(tpke.deserialize1(share))
                    elif 'ACS_RBC' == op_type:
                        des_op_msg = pickle.loads(op_msg.payload)
                    elif 'ACS_ABA' == op_type:
                        des_op_msg = pickle.loads(op_msg.payload)
                    else:
                        print(f'Unknown message type {o}')
                    
                    # message o has format (round_id, ('Header', dest_id, payload))
                    o = (round_id, (op_type, msg_id, des_op_msg))
                    # print(f"Recv round {o[0]}: [{src_id} -> {j}]")
                    # print("recved", o)
                    return (src_id, o)
                except Empty:
                    # print(f"Node {j} receiving timeout")
                    time.sleep(0)

        return _recv

    return makeSend(pid), makeRecv()

def initiateThresholdSig(f):
    # global PK, SKs
    # print contents
    (l, k, sVK, sVKs, SKs) = pickle.load(f)
    return boldyreva.TBLSPublicKey(l, k, boldyreva.deserialize2(sVK), [boldyreva.deserialize2(sVKp) for sVKp in sVKs]), \
           [boldyreva.TBLSPrivateKey(l, k, boldyreva.deserialize2(sVK), [boldyreva.deserialize2(sVKp) for sVKp in sVKs], \
                           boldyreva.deserialize0(SKp[1]), SKp[0]) for SKp in SKs]

def initiateThresholdEnc(f):
    # global encPK, encSKs
    (l, k, sVK, sVKs, SKs) = pickle.load(f)
    return TPKEPublicKey(l, k, deserialize1(sVK), [deserialize1(sVKp) for sVKp in sVKs]), \
           [TPKEPrivateKey(l, k, deserialize1(sVK), [deserialize1(sVKp) for sVKp in sVKs], \
                           deserialize0(SKp[1]), SKp[0]) for SKp in SKs]

# def submit(badger):
#     time.sleep(4)
#     badger.submit_tx('<[HBBFT Input from 0]>')
#     time.sleep(5)
#     badger.submit_tx('<[HBBFT Input from 1]>')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("N", help="Number of nodes")
    parser.add_argument("f", help="Max number of fault")
    parser.add_argument("pid", help="pid of node")
    parser.add_argument("threshold_sig_keys", help="location of threshold signature keys")
    parser.add_argument("threshold_enc_keys", help="location of threshold encryption keys")
    args = parser.parse_args()

    # initiate honeybadgerBFT
    sid = "sidA"
    N = int(args.N)
    f = int(args.f)
    B = 1
    pid = int(args.pid)
    
    PK, SKs = initiateThresholdSig(open(args.threshold_sig_keys, "rb"))
    encPK, encSKs = initiateThresholdEnc(open(args.threshold_enc_keys, "rb"))
    initializeGIPC(PK)

    send, recv = router(pid)

    badger = HoneyBadgerBFT(
        sid, pid, 1, N, f, PK, SKs[pid], encPK, encSKs[pid], send, recv
    )
    time.sleep(5)

    # if pid == 0:
    #     x = threading.Thread(target=submit, args=(badger,))
    #     x.start()

    thread = gevent.spawn(badger.run)

    try:
        gevent.joinall([thread])
    except KeyboardInterrupt:
        gevent.killall([thread])
        raise