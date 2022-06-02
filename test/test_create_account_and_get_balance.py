import time
from hbbft.client.user_service_client import UserServiceClient


def test_create_account():
    time.sleep(10)
    client = UserServiceClient(ip="172.16.238.2", num=2)
    assert len(client.accts) == 2
    acct = client.get_balance(client.accts[0].account_id)
    assert client.accts[0].balance == acct.balance
    client.close()


def test_get_balance():
    time.sleep(10)
    client = UserServiceClient(ip="172.16.238.2", num=2)
    client.create_txns(1)
    acct0 = client.get_balance(client.accts[0].account_id)
    acct1 = client.get_balance(client.accts[1].account_id)
    while acct0.balance == int(1e9) or acct1.balance == int(1e9):
        time.sleep(5)
        acct0 = client.get_balance(client.accts[0].account_id)
        acct1 = client.get_balance(client.accts[1].account_id)
    assert abs(client.accts[0].balance - client.accts[1].balance) == abs(acct0.balance - acct1.balance)
    client.close()


if __name__ == "__main__":
    test_create_account()
    test_get_balance()
