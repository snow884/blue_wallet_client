# Blue Wallet API Client
Bitcoin lightning wallet for python. A Python client for the API of custodial Bitcoin Lightning wallet called Blue Wallet.

## Intro

Many merchant wallets for Bitcoin Lightning require KYC or other cumbersome registration steps. This package provides developer 
with an API wrapper for the Blue Wallet API enabling rapid development of code without the need to wait for KYC.

This API is meant for smaller hobby projects that aim to process hundreds or thousands of payments a month. For applications requiring more throughput please use a paid commercial solution.

## Installation

You can install this package by running 
```
pip install blue_wallet_client
```

## Usage

The file example.py shows how to use the API client to send and receive Lightning payments.


Import the client class
```
from blue_wallet_client import BlueWalletClient
```

Obtain the wallet credentials by running 
```
credentials = BlueWalletClient().get_login()
print(credentials)
```

Alternatively you can read the recovery QR code of your existing Blue wallet. The QR code contains the login and password in plan text separated by the colon symbol.

Log into the wallet and initialize the client object. Replace xxx and yyy with your correct credentials.
```
bw_clinet = BlueWalletClient(bluewallet_login="xxx", bluewallet_password="yyy")
```

To get information about the lightning node used by Blue wallet run 
```
node_info = bw_clinet.get_node_info()
print(node_info)
```
This is a great way to verify that the API works.

Get on-chain address of your wallet by running:
```
on_chain_address = bw_clinet.get_on_chain_address()
print(on_chain_address)
```

This address is a way you can top up your wallet from an on-chain wallet.

To check the ballance in your wallet run
```
balance_btc = bw_clinet.balance()
print(balance_btc)
```

To generate a lightning invoice for 100 satoshi run
```
res_dict = bw_clinet.create_invoice(amt=100, memo="send money to your address")
payment_request = res_dict["payment_request"]
r_hash = res_dict["r_hash"]
print(f"Generated an invoice: \n {payment_request}")
```

`payment_request` will be send to the payer, make sure to store r_hash as this is the primary key to later find the invoice in the invoice database.

To check the status of the invoice run 
```
res = bw_clinet.lookup_invoice(r_hash=r_hash)
print(res)
print(res["ispaid"])
```

Wait until the value under the key 'ispaid' turns to True. Check if the invoice is expired.

To pay a lightning invoice run
```
payment_request = 'lnbc300n1p3nekenpp5atr3s2csqtamzaw4mzqm9e7h7wfyz5j60ffuu07ajmgzk3zxatdqdq5w3jhxapqd9h8vmmfvdjscqzpgxqyz5vqsp5npd8t9rnukewm4sz3zwej8eupjuytjayneg9aw0dyuynwszpcurq9qyyssqdtnlkmynnahjspqj5sde5v0z9tzke80xvw8rsjapl7kfrvp6pqnk9qsdfhswnmeu55cav006p8j6k86ed9zkaunc6rx79s5cwjd7epsq4aektn'
bw_clinet.payinvoice(payment_request)
```
The invoice should be paid almost instantly. 

The class also supports sending of payments to a lightning address as defined by André Neves https://github.com/andrerfneves/lightning-address/blob/master/README.md .

In order to send Bitcoin to the lightning address use the `sendtoaddress` method 

```
bw_clinet.sendtoaddress(lightning_address='adamivansky53@zbd.gg', amount=50, message='test send of 50 satoshis' )
```

## Other notes

The Blue wallet API struggles once the number of invoices reaches about 1000. 

