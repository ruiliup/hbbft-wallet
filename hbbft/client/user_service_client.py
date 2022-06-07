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
    def __init__(self, ip: str = 'localhost', port: int = 50051, num: int = 100, mode: int = 0):
        self.ip = ip
        self.port = port
        self.num = num
        self.mode = mode
        self.accts = []
        self.channel = grpc.insecure_channel(f'{self.ip}:{self.port}')
        self.stub = user_service_pb2_grpc.UserServiceStub(self.channel)
        if self.mode == 0:
            self.create_accts()

    def close(self):
        self.channel.close()

    def create_accts(self):
        print(f"###Creating total {self.num} accounts...")
        for _ in range(self.num):
            if self.mode == 0:
                name = ''.join(choices(ascii_letters, k=4))
                balance = int(1e9)
            elif self.mode == 1:
                name = input("###Enter your name to create a new account ###: ")
                balance = int(input(
                    "###Enter the initial balance for this new account (input an integer) ###: "))

            acct_id = randint(1, 1000)
            print(f'create account: {acct_id} {name} {balance}', flush=True)
            self.accts.append(self.create_account(acct_id, name, balance))

    def create_account(self, account_id: int, name: str, balance: int):
        response = self.stub.Register(
            user_service_pb2.Account(
                account_id=account_id, user_name=name, balance=balance)
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

    def update_acct(self):
        request = user_service_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
        response = self.stub.GetAccountsCall(request)
        acct_list = []
        for acct in response.accounts:
            # print("TEST", acct)
            acct_list.append(acct)
        self.accts = acct_list

    def pick_acct(self):
        self.update_acct()
        if self.mode == 0:
            return choice(self.accts)
        print(f"These are all the accounts that we have: \n")
        for i in range(len(self.accts)):
            print(f"{i}. {self.accts[i]}\n")
        no = input("###Choose one account ###: ")
        return self.accts[int(no)]

    def create_txns(self, num):
        states = []
        print(f"###Creating total {num} transactions...###")
        for _ in range(num):
            print(f"####Creating a transaction, no. {_}####")
            s = self.create_txn()
            states.append(s)
        return states

    def create_txn(self):
        print("Origin Account")
        from_acct = self.pick_acct()
        print(f"Chosen origin account: {from_acct}")
        print("Destination Account")
        to_acct = self.pick_acct()
        print(f"Chosen destination account: {to_acct}")
        while from_acct is to_acct:
            print(
                f"Origin Account and Destination account cannot be the same, choose destination account again: ")
            to_acct = self.pick_acct()
            print(f"Chosen destination account: {to_acct}")

        return self._create_txn(from_acct, to_acct)

    def _create_txn(self, from_acct, to_acct):
        """
        todo: check balance for each account once we are able to get balance.
        """
        if self.mode == 0:
            pay_amount = randint(0, 100)
        elif self.mode == 1:
            pay_amount = int(
                input("Input the amount of money that you want to transfer (an integer): "))
        # Select two users
        response = self.stub.PayToCall(
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
        # print(f"Get Balance for Account ID: {acct_id}")
        response = self.stub.GetBalanceCall(
            user_service_pb2.GetBalanceRequest(account_id=acct_id)
        )
        # print(f"After getting balance: {response.account.balance}")
        return response.account

    def get_all_balance(self):
        self.update_acct()
        for acct in self.accts:
            self.get_balance(acct.account_id)
