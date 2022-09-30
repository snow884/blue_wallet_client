import time

from blue_wallet_client import BlueWalletClient


def sign_up():
    """
    Use this method to create a Blue Wallet account.

    Alternatively you can read the recovery QR code
    generated by blue wallet and get the
    username and password from there
    """

    credentials = BlueWalletClient().get_login()
    print(credentials)


def send_receive_payment():
    """
    This method demonstrates the functionality of this client
    """
    # replace xxx and yyy with credentials obtained from the sign_up method
    bw_clinet = BlueWalletClient(bluewallet_login="xxx", bluewallet_password="yyy")

    node_info = bw_clinet.get_node_info()

    print("Here is the info on the Lightning Node used by Blue wallet:")
    print(node_info)

    on_chain_address = bw_clinet.get_on_chain_address()

    print("Here is the onchain address of your wallet:")
    print(on_chain_address)

    balance_btc = bw_clinet.balance()

    print("Here is your current balance:")
    print(balance_btc)

    res_dict = bw_clinet.create_invoice(amt=100, memo="send money to your address")

    payment_request = res_dict["payment_request"]
    r_hash = res_dict["r_hash"]

    print(f"Generated an invoice: \n {payment_request}")

    print("Waiting for the invoice to be paid...")

    ispaid = False

    while not ispaid:

        res = bw_clinet.lookup_invoice(r_hash=r_hash)

        ispaid = res["ispaid"]

        time.sleep(60)

    print("The wallet will now pay an invoice.")

    payment_request = input("Please specify the invoice you want to pay: ")

    bw_clinet.payinvoice(payment_request)

    time.sleep(5)

    print("Here is your current balance:")
    print(balance_btc)
