import json
from collections import namedtuple
from enum import Enum

import gevent
import os
from gevent.queue import Queue
import grpc
import hashlib
import time
import random
from datetime import datetime
from hbbft.common.protos import user_service_pb2, user_service_pb2_grpc
from hbbft.common.setting import user_service_port

from honeybadgerbft.core.commoncoin import shared_coin
from honeybadgerbft.core.binaryagreement import binaryagreement
from honeybadgerbft.core.reliablebroadcast import reliablebroadcast
from honeybadgerbft.core.commonsubset import commonsubset
from honeybadgerbft.core.honeybadger_block import honeybadger_block
from honeybadgerbft.exceptions import UnknownTagError

from google.protobuf.json_format import MessageToJson, Parse


class BroadcastTag(Enum):
    ACS_COIN = 'ACS_COIN'
    ACS_RBC = 'ACS_RBC'
    ACS_ABA = 'ACS_ABA'
    TPKE = 'TPKE'


BroadcastReceiverQueues = namedtuple(
    'BroadcastReceiverQueues', ('ACS_COIN', 'ACS_ABA', 'ACS_RBC', 'TPKE'))


def broadcast_receiver(recv_func, recv_queues):
    sender, (tag, j, msg) = recv_func()
    if tag not in BroadcastTag.__members__:
        # TODO Post python 3 port: Add exception chaining.
        # See https://www.python.org/dev/peps/pep-3134/
        raise UnknownTagError('Unknown tag: {}! Must be one of {}.'.format(
            tag, BroadcastTag.__members__.keys()))
    recv_queue = recv_queues._asdict()[tag]

    if tag != BroadcastTag.TPKE.value:
        recv_queue = recv_queue[j]

    recv_queue.put_nowait((sender, msg))


def broadcast_receiver_loop(recv_func, recv_queues):
    while True:
        broadcast_receiver(recv_func, recv_queues)


class HoneyBadgerBFT():
    r"""HoneyBadgerBFT object used to run the protocol.

    :param str sid: The base name of the common coin that will be used to
        derive a nonce to uniquely identify the coin.
    :param int pid: Node id.
    :param int B: Batch size of transactions.
    :param int N: Number of nodes in the network.
    :param int f: Number of faulty nodes that can be tolerated.
    :param str sPK: Public key of the threshold signature
        (:math:`\mathsf{TSIG}`) scheme.
    :param str sSK: Signing key of the threshold signature
        (:math:`\mathsf{TSIG}`) scheme.
    :param str ePK: Public key of the threshold encryption
        (:math:`\mathsf{TPKE}`) scheme.
    :param str eSK: Signing key of the threshold encryption
        (:math:`\mathsf{TPKE}`) scheme.
    :param send:
    :param recv:
    """

    def __init__(self, sid, pid, B, N, f, sPK, sSK, ePK, eSK, send, recv, block_path):
        self.sid = sid
        self.pid = pid
        self.B = B
        self.N = N
        self.f = f
        self.sPK = sPK
        self.sSK = sSK
        self.ePK = ePK
        self.eSK = eSK
        self._send = send
        self._recv = recv

        self.round = 0  # Current block number
        self.transaction_buffer = []
        self.block_path = block_path
        self.block_size = 100
        self._per_round_recv = {}  # Buffer of incoming messages
        self.balance_cache = {} # dictionary to store balance of all users that routes to this node

    def get_txn(self, user_service_port):
        # test get transactions from grpc.
        with grpc.insecure_channel(f'localhost:{user_service_port}') as channel:
            # fetch this txn from grpc to hbbft.
            stub2 = user_service_pb2_grpc.UserServiceStub(channel)
            request = user_service_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
            txns = stub2.GetTransactions(request)
            for txn in txns:
                print('Get_tx', txn, flush=True)
                txn_s = MessageToJson(txn, indent=False).replace('\n', '')
                # print('Changed to txn_s', txn_s, flush=True)
                self.submit_tx(txn_s)
            # DELETE For test:
            #     self.save_block(txn_s)
            # self.read_block()

    def submit_tx(self, tx):
        """Appends the given transaction to the transaction buffer.

        :param tx: Transaction to append to the buffer.
        """
        # print('submit_tx', self.pid, tx, '\n', flush=True)
        self.transaction_buffer.append(tx)

    def save_block(self, tx):
        print(f'save block: {tx}', flush=True)
        if not os.path.exists(self.block_path):
            os.makedirs(self.block_path)
        if os.listdir(self.block_path):
            last_file = sorted(os.listdir(self.block_path))[-1]
            f = open(os.path.join(self.block_path, last_file), 'r')
            if len(f.readlines()) < self.block_size + 1:  # one line for hash
                with open(os.path.join(os.path.join(self.block_path, last_file)), 'a') as wf:
                    # json.dump(tx, wf)
                    wf.write(tx + '\n')
                    return
        else:
            last_file = None

        timestamp_file = time.time()
        with open(os.path.join(self.block_path, str(timestamp_file)), 'w') as wf:
            if last_file:
                with open(os.path.join(self.block_path, last_file), 'rb') as rf:
                    bytes = rf.read()
                    readable_hash = hashlib.sha256(bytes).hexdigest()
            else:
                readable_hash = hashlib.sha256(str("genesis_block").encode('utf-8')).hexdigest()
            # print("write readable_hash", readable_hash)
            wf.write(readable_hash + '\n')
            wf.write(tx + '\n')
        return

    @staticmethod
    def read_block(block_path):
        for file in os.listdir(block_path):
            with open(os.path.join(block_path, file), 'r') as f:
                # TODO: Check the hash matches previous block file's content
                txns = f.readlines()
                for tx in txns[1:]:
                    tx_message = Parse(tx, user_service_pb2.UserTransaction())
                    yield tx_message

    @staticmethod
    def get_balance(block_path, acct_id: int):
        user_name, balance = '', 0
        print(f'get balance for {acct_id}', flush=True)
        for tx_message in HoneyBadgerBFT.read_block(block_path):
            print(f"get balance: read from block: {tx_message}", flush=True)
            if tx_message.HasField('account') and acct_id == tx_message.account.account_id:
                balance += tx_message.account.balance
                user_name = tx_message.account.user_name
            elif tx_message.HasField('transaction'):
                if acct_id == tx_message.transaction.src_acct.account_id:
                    balance -= tx_message.transaction.amount
                    user_name = tx_message.transaction.src_acct.user_name
                elif acct_id == tx_message.transaction.des_acct.account_id:
                    balance += tx_message.transaction.amount
                    user_name = tx_message.transaction.des_acct.user_name
        print(f'Get balance: {user_name} {balance}', flush=True)
        return user_service_pb2.Account(account_id=acct_id, user_name=user_name, balance=balance)

    def run(self):
        """Run the HoneyBadgerBFT protocol."""

        def _recv():
            """Receive messages."""
            while True:
                (sender, (r, msg)) = self._recv()

                # Maintain an *unbounded* recv queue for each epoch
                if r not in self._per_round_recv:
                    # Buffer this message
                    assert r >= self.round  # pragma: no cover
                    self._per_round_recv[r] = Queue()

                _recv = self._per_round_recv[r]
                if _recv is not None:
                    # Queue it
                    _recv.put((sender, msg))

                # else:
                # We have already closed this
                # round and will stop participating!

        self._recv_thread = gevent.spawn(_recv)
        random.seed()

        while True:
            start = datetime.now()
            # For each round...
            r = self.round
            if r not in self._per_round_recv:
                self._per_round_recv[r] = Queue()

            # Select all the transactions (TODO: actual random selection)
            # tx_to_send = self.transaction_buffer[:self.B]
            tx_to_send = []
            if len(self.transaction_buffer) > self.B:
                tx_to_send = random.sample(self.transaction_buffer, self.B)
            else:
                tx_to_send = self.transaction_buffer[::]
            print(f"tx_to_send number: {len(tx_to_send)}")
            # TODO: Wait a bit if transaction buffer is not full
            self.get_txn(user_service_port)

            # Run the round
            def _make_send(r):
                def _send(j, o):
                    self._send(j, (r, o))

                return _send

            send_r = _make_send(r)
            recv_r = self._per_round_recv[r].get
            tx = "||".join(tx_to_send)
            
            # if len(tx_to_send) > 0:
            #     decoded_tx = Parse(tx_to_send[0], user_service_pb2.PayToRequest())
            #     src_account = decoded_tx.src_acct.user_name
            #     if src_account in self.balance_cache.keys() and self.balance_cache[src_account] >= decoded_tx.amount:
            #         tx = tx_to_send[0]

            new_tx = self._run_round(r, tx, send_r, recv_r)
            # print('new_tx:', new_tx, flush=True)

            # write transactions to block files
            new_single_tx = []
            for tx in new_tx:
                if tx:
                    batch = tx.decode().split("||")
                    for single_tx in batch:
                        self.save_block(single_tx)
                        new_single_tx.append(single_tx)

            # Remove all of the new transactions from the buffer
            self.transaction_buffer = [_tx for _tx in self.transaction_buffer if _tx not in new_single_tx]

            # update balance cache
            # TODO: support batched transaction process
            # if new_tx[self.pid]:
            #     decoded_tx = Parse(new_tx[self.pid], user_service_pb2.PayToRequest())
            #     src_account = decoded_tx.src_acct.user_name
            #     if src_account in self.balance_cache.keys():
            #         self.balance_cache[src_account] -= decoded_tx.amount
            #     else:
            #         self.balance_cache[src_account] = 10000 - decoded_tx.amount

            # for tx in new_tx:
            #     if tx:
            #         decoded_tx =  Parse(tx, user_service_pb2.PayToRequest())
            #         dst_account = decoded_tx.des_acct.user_name
            #         if dst_account in self.balance_cache.keys():
            #             self.balance_cache[dst_account] += decoded_tx.amount

            # print("balances: ", self.balance_cache, flush=True)
            end = datetime.now()
            print(f"Node {self.pid}: time for round {self.round}: {end - start}. Total transactions: {len(new_single_tx)} ", flush=True)

            self.round += 1  # Increment the round
            # if self.round >= 3:
            #     break   # Only run one round for now

    def _run_round(self, r, tx_to_send, send, recv):
        """Run one protocol round.

        :param int r: round id
        :param tx_to_send: Transaction(s) to process.
        :param send:
        :param recv:
        """
        # Unique sid for each round
        sid = self.sid + ':' + str(r)
        pid = self.pid
        N = self.N
        f = self.f

        def broadcast(o):
            """Multicast the given input ``o``.

            :param o: Input to multicast.
            """
            for j in range(N):
                send(j, o)

        # Launch ACS, ABA, instances
        coin_recvs = [None] * N
        aba_recvs = [None] * N  # noqa: E221
        rbc_recvs = [None] * N  # noqa: E221

        aba_inputs = [Queue(1) for _ in range(N)]  # noqa: E221
        aba_outputs = [Queue(1) for _ in range(N)]
        rbc_outputs = [Queue(1) for _ in range(N)]

        my_rbc_input = Queue(1)
        # print(pid, r, 'tx_to_send:', tx_to_send)

        def _setup(j):
            """Setup the sub protocols RBC, BA and common coin.

            :param int j: Node index for which the setup is being done.
            """

            def coin_bcast(o):
                """Common coin multicast operation.

                :param o: Value to multicast.
                """
                broadcast(('ACS_COIN', j, o))

            coin_recvs[j] = Queue()
            coin = shared_coin(sid + 'COIN' + str(j), pid, N, f,
                               self.sPK, self.sSK,
                               coin_bcast, coin_recvs[j].get)

            def aba_bcast(o):
                """Binary Byzantine Agreement multicast operation.

                :param o: Value to multicast.
                """
                broadcast(('ACS_ABA', j, o))

            aba_recvs[j] = Queue()
            gevent.spawn(binaryagreement, sid + 'ABA' + str(j), pid, N, f, coin,
                         aba_inputs[j].get, aba_outputs[j].put_nowait,
                         aba_bcast, aba_recvs[j].get)

            def rbc_send(k, o):
                """Reliable broadcast operation.

                :param o: Value to broadcast.
                """
                send(k, ('ACS_RBC', j, o))

            # Only leader gets input
            rbc_input = my_rbc_input.get if j == pid else None
            rbc_recvs[j] = Queue()
            rbc = gevent.spawn(reliablebroadcast, sid + 'RBC' + str(j), pid, N, f, j,
                               rbc_input, rbc_recvs[j].get, rbc_send)
            rbc_outputs[j] = rbc.get  # block for output from rbc

        # N instances of ABA, RBC
        for j in range(N):
            _setup(j)

        # One instance of TPKE
        def tpke_bcast(o):
            """Threshold encryption broadcast."""
            broadcast(('TPKE', 0, o))

        tpke_recv = Queue()

        # One instance of ACS
        acs = gevent.spawn(commonsubset, pid, N, f, rbc_outputs,
                           [_.put_nowait for _ in aba_inputs],
                           [_.get for _ in aba_outputs])

        recv_queues = BroadcastReceiverQueues(
            ACS_COIN=coin_recvs,
            ACS_ABA=aba_recvs,
            ACS_RBC=rbc_recvs,
            TPKE=tpke_recv,
        )
        gevent.spawn(broadcast_receiver_loop, recv, recv_queues)

        _input = Queue(1)
        _input.put(tx_to_send)
        return honeybadger_block(pid, self.N, self.f, self.ePK, self.eSK,
                                 _input.get,
                                 acs_in=my_rbc_input.put_nowait, acs_out=acs.get,
                                 tpke_bcast=tpke_bcast, tpke_recv=tpke_recv.get)
