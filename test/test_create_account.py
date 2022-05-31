from hbbft.client.user_service_client import UserServiceClient


def test_create_account():
    client = UserServiceClient(ip="172.16.238.2", num=2)
    client.close()
    assert len(client.accts) == 2
    assert client.accts[0].balance == client.get_balance(client.accts[0].account_id)


def test_get_balance():
    client = UserServiceClient(ip="172.16.238.2", num=2)
    client.create_txns(1)
    client.close()
    assert abs(client.accts[0].balance - client.accts[1].balance) == abs(client.get_balance(client.accts[0].account_id) - client.get_balance(client.accts[1].account_id))





