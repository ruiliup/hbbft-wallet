from hbbft.client.user_service_client import UserServiceClient
import time

if __name__ == "__main__":
    mode = input("Choose interactive mode(0) or autumatic mode(1).")
    if mode == 1:
        time.sleep(3)
        client = UserServiceClient(ip="172.16.238.2", num=2)
        client.create_txns(2)
        client.close()
        client = UserServiceClient(ip="172.16.238.3", num=4)
        client.create_txns(2)
        client.close()
        client = UserServiceClient(ip="172.16.238.4", num=4)
        client.create_txns(2)
        client.close()
        client = UserServiceClient(ip="172.16.238.5", num=4)
        client.create_txns(2)
        client.close()
    else:
        Login_status = False
        while(True):
            if not Login_status:
                print("###Welcome! Please Log in!###")
                print("###IP List:###")
                print("172.16.238.2\n 172.16.238.3\n 172.16.238.4\n 172.16.238.5\n")
                ip_in = input("###Input the ip that you want to log in to:###")
                num_in = int(input(
                    "###Input the number of accounts you want to create:####"))
                client = UserServiceClient(ip=ip_in, num=num_in)
                Login_status = True
            else:
                while(True):
                    print(f"1. Create {client.num} New Accounts.")
                    print("2. Create one transaction.")
                    print("3. Get Balance")
                    print("3. Log out")
                    action = input("###Choose your action: ###")
                    if action == "1":
                        client.create_accts()
                    elif action == "2":
                        client.create_txns(1)
                    elif action == "3":
                        client.close()
                        Login_status = False
                        break
