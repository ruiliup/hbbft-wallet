"""
Honeybadger has recv function to receive transactions from external.
We implement function here to feed this recv so Honeybadger can process those transactions.
"""
import grpc
import time
from random import randint, choice, choices
from string import ascii_letters
from hbbft.common.protos import user_service_pb2, user_service_pb2_grpc


class UserServiceClient(object):
    def __init__(self, ip: str = 'localhost', port: int = 50051, num: int = 100):
        self.ip = ip
        self.port = port
        self.num = num
        self.accts = []
        self.create_accts()
        self.channel = grpc.insecure_channel(f'{self.ip}:{self.port}')
        self.stub = user_service_pb2_grpc.UserServiceStub(self.channel)

    def close(self):
        self.channel.close()

    def create_accts(self):
        for _ in range(self.num):
            acct_id = randint(0, self.num - 1)
            name = ''.join(choices(ascii_letters, k=4))
            balance = int(1e9)
            self.accts.append(self.create_account(acct_id, name, balance))

    @staticmethod
    def create_account(account_id: int, name: str, balance: int):
        return user_service_pb2.Account(account_id=account_id, user_name=name, balance=balance)

    def pick_acct(self):
        return choice(self.accts)

    def create_txns(self, num):
        states = []
        for _ in range(num):
            s = self.create_txn()
            states.append(s)
        return states

    def create_txn(self):
        from_acct = self.pick_acct()
        to_acct = self.pick_acct()
        while from_acct is to_acct:
            to_acct = self.pick_acct()
        return self._create_txn(self.stub, from_acct, to_acct)

    def _create_txn(self, stub, from_acct, to_acct):
        """
        todo: check balance for each account once we are able to get balance.
        """
        pay_amount = randint(0, 100)
        # Select two users

        response = stub.PayToCall(
            user_service_pb2.PayToRequest(
                src_acct=from_acct,
                des_acct=to_acct,
                amount=pay_amount,
                timestamp=time.time()
            )
        )
        from_acct.balance -= pay_amount
        to_acct.balance += pay_amount
        return response.status
