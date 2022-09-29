import time

from blue_wallet_client import BlueWalletClient


def sign_up():

    credentials = BlueWalletClient().get_login()
    print(credentials)


def send_receive_payment():

    bw_clinet = BlueWalletClient(bluewallet_login="xxx", bluewallet_password="xxx")

    node_info = bw_clinet.get_node_info()

    print(node_info)

    on_chain_address = bw_clinet.get_on_chain_address()

    print(on_chain_address)

    balance_btc = bw_clinet.balance()

    print(balance_btc)

    res_dict = bw_clinet.create_invoice(amt=100, memo="send money to your address")

    payment_request = res_dict["payment_request"]
    r_hash = res_dict["r_hash"]

    print(f"Generated an invoice: \n {payment_request}")

    print(f"Waiting for the invoice to be paid...")

    ispaid = False

    while not ispaid:

        res = bw_clinet.lookup_invoice(r_hash=r_hash)

        ispaid = res["ispaid"]

        time.sleep(60)

    print(res)

    payment_request = input("Please specify the invoice you want to pay: ")

    bw_clinet.payinvoice(payment_request)

    time.sleep(5)

    print(balance_btc)
