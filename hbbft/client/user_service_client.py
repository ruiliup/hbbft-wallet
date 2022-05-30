"""
Honeybadger has recv function to receive transactions from external.
We implement function here to feed this recv so Honeybadger can process those transactions.
"""
import datetime

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
        self.channel = grpc.insecure_channel(f'{self.ip}:{self.port}')
        self.stub = user_service_pb2_grpc.UserServiceStub(self.channel)
        self.create_accts()

    def close(self):
        self.channel.close()

    def create_accts(self):
        for _ in range(self.num):
            acct_id = randint(1, 1000)
            name = ''.join(choices(ascii_letters, k=4))
            balance = int(1e9)
            print(f'create account: {acct_id} {name} {balance}', flush=True)
            self.accts.append(self.create_account(acct_id, name, balance))

    def create_account(self, account_id: int, name: str, balance: int):
        response = self.stub.Register(
            user_service_pb2.Account(account_id=account_id, user_name=name, balance=balance)
        )
        status = False
        if response.status:
            # call get balance and verify account and balance match.
            now = datetime.datetime.now()
            end = now + datetime.timedelta(minutes=10)
            acct = self.get_balance(account_id)
            while now <= end and acct.balance == 0:
                time.sleep(5)
                acct = self.get_balance(account_id)
            if acct.account_id == account_id and acct.user_name == name and acct.balance == balance:
                status = True
        if status:
            print(f'successfully created account for {name}', flush=True)
            return user_service_pb2.Account(account_id=account_id, user_name=name, balance=balance)
        else:
            print(f'failed to create account for {name}')
            return None

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

    def get_balance(self, acct_id):
        response = self.stub.GetBalanceCall(
            user_service_pb2.GetBalanceRequest(account_id=acct_id)
        )
        return response.account
