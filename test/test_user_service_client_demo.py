from hbbft.client.user_service_client import UserServiceClient
import time

if __name__ == "__main__":
    Login_status = False
    while(True):
        if not Login_status:
            print("###Welcome! Please Log in!###")
            print("###IP List:###")
            # print(
            #     "1. 172.16.238.2\n2. 172.16.238.3\n3. 172.16.238.4\n4. 172.16.238.5\n")
            ip_list = ["172.16.238.2", "172.16.238.3", "172.16.238.4", "172.16.238.5"]
            for i in range(len(ip_list)):
                print(f"{i}: {ip_list[i]}")
            ip_in = int(input(
                "###Input the ip address that you want to log in to ###: "))
            num_in = int(input(
                "###Input the number of accounts you want to create ####: "))
            client = UserServiceClient(ip=ip_list[ip_in], num=num_in, mode=1)
            Login_status = True
        else:
            while(True):
                print(f"1. Create {client.num} New Accounts.")
                print("2. Create a new transaction.")
                print("3. Get Balance")
                print("4. Log out")
                action = input("###Choose your action: (Input the number) ###: ")
                if action == "1":
                    client.create_accts()
                elif action == "2":
                    client.create_txns(1)
                elif action == "3":
                    client.update_acct()
                    print("Here are all the accounts that we have:")
                    for enum in range(len(client.accts)):
                        print(
                            f"{enum}. {client.accts[enum].account_id}, {client.accts[enum].user_name}\n")
                    acct_no = int(input(
                        "###Choose the account that you want to get balance for ###: "))
                    acct = client.get_balance(client.accts[acct_no].account_id)
                    print(f"\nAvailable balance for this account: {acct.balance}\n")
                elif action == "4":
                    print("Logging out...")
                    client.close()
                    Login_status = False
                    break
