"""
Blue wallet client
"""
import base64

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

ROOT_URL = "https://lndhub.herokuapp.com"


class CredentialsMissingException(Exception):
    """
    Exception class for missing credentials error
    """


class RateLimitExceededException(Exception):
    """
    Exception class for rate limit exceeded error
    """


class BlueWalletClient:
    """
    A client for the blue wallet API allowing developers to operate a
    Bitcoin Lightning wallet
    """

    def __init__(self, bluewallet_login: str = None, bluewallet_password: str = None):
        """
        Initiate the Blue wallet client.

        Args:
            bluewallet_login (str, optional): The username to your Blue wallet or
                the username generated from get_login. Defaults to None.
            bluewallet_password (str, optional): The password to your Blue wallet or
                the username generated from get_login. Defaults to None.
        """
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
            method_whitelist=["GET", "POST"],
            backoff_factor=10,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.http = requests.Session()
        self.http.mount("https://", adapter)
        self.http.mount("http://", adapter)

        if (not bluewallet_login) and (not bluewallet_password):
            self.creds = None
            return

        self.creds = {
            "login": bluewallet_login,
            "password": bluewallet_password,
        }

        self.get_token()

    def _check_login(fcn: object):
        def debug_wrapper(self, *args, **kwargs):

            if not self.creds:
                raise CredentialsMissingException(
                    f"""
                    The method {fcn} requires that class is 
                    initialized with login and password.
                    """
                )

            return fcn(self, *args, **kwargs)

        return debug_wrapper

    @_check_login
    def refresh_invoices(self, limit: int = 1000):
        """
        Refresh the internal list of invoices

        Args:
            limit (limit, optional): Number of historical invoices to load
        """
        invoice_list = self.getuserinvoices_paginate(limit)
        self.invoice_lookup = {
            inv_data["r_hash"]: inv_data for inv_data in invoice_list
        }

    def get_login(self):
        """
        Register a new Blue wallet account and return a dictionary
        containing credential

        Args:
            limit (limit, optional): Number of historical invoices to load
        """
        body = {"partnerid": "bluewallet", "accounttype": "common"}

        res = self.http.post(f"{ROOT_URL}/create", data=body)
        res.raise_for_status()

        return res.json()

    @_check_login
    def _check_limit_reached(self, headers: dict):

        if int(headers.get("X-Ratelimit-Remaining", 100)) < 10:
            raise RateLimitExceededException(
                f"""
                Rate limit dropped below {int(headers['X-Ratelimit-Remaining'])}, 
                headers: {headers}
                """
            )

    @_check_login
    def get_token(self):
        """
        Obtain the access and refresh token and store it in client

        Args:
        """
        res = self.http.post(f"{ROOT_URL}/auth", data=self.creds)
        self._check_limit_reached(res.headers)
        res.raise_for_status()
        res_dict = res.json()

        self.access_token = res_dict["access_token"]
        self.refresh_token = res_dict["refresh_token"]

    @_check_login
    def create_invoice(self, amt: int, memo: str) -> dict:
        """
        Create a new lightning invoice

        Args:
            amt (int): Amount to be requested in Satoshis (1e-8 of 1 Bitcoin)
            memo (str): Payment description that is visible to you and the person receiving the
                payment

        Returns:
            dict: Details of the invoice generated
        """
        body = {"amt": amt, "memo": memo}
        res = self.http.post(
            f"{ROOT_URL}/addinvoice",
            data=body,
            headers={"Authorization": f"{self.access_token}"},
        )
        self._check_limit_reached(res.headers)
        res.raise_for_status()
        res_dict = res.json()
        res_dict = self.correct_rhash(res_dict)
        return res_dict

    @_check_login
    def payinvoice(self, payment_request: str, amount: int = None):
        """
        Pay a lightning invoice

        Args:
            payment_request (str): Payment request
            amount (int, optional): Option to specify the amount to send.
                Defaults to None.

        Returns:
        """
        body = {"invoice": payment_request}
        if amount:
            body["amount"] = amount

        res = self.http.post(
            f"{ROOT_URL}/payinvoice",
            data=body,
            headers={"Authorization": f"{self.access_token}"},
        )
        self._check_limit_reached(res.headers)
        res.raise_for_status()

        res_dict = res.json()

        if res_dict.get("error", None):
            raise Exception(
                f"""
                Error paying the invoice '{payment_request}': 
                {res_dict.get('message','')}, code: {res_dict.get('code','')}
                """
            )

    @_check_login
    def getuserinvoices(self, limit: int) -> dict:
        """
        Get all invoices of the user that is currently
        logged in.

        Args:
            limit (int): Maximum number of invoices to retrieve

        Returns:
            dict: Dict containing the retrieved invoices
        """
        params = {"limit": limit}

        res = self.http.get(
            f"{ROOT_URL}/getuserinvoices",
            params=params,
            headers={"Authorization": f"{self.access_token}"},
        )
        self._check_limit_reached(res.headers)
        res.raise_for_status()
        res_dict = res.json()
        return res_dict

    @_check_login
    def getuserinvoices_paginate(self, limit: int = 1000):
        """
        Get all invoices of the user that is currently
        logged in and paginate over them to retrieve
        all invoices that the user has.

        Args:
            limit (int, optional): Maximum number of invoices to retrieve
                per pagination. Defaults to 1000.

        Returns:
            dict: Dict containing the retrieved invoices
        """
        res = []
        res_full = []

        res = self.getuserinvoices(limit)

        res_full.extend(res)

        for invoice_data in res_full:
            invoice_data = self.correct_rhash(invoice_data)

        return res_full

    @_check_login
    def lookup_invoice(self, r_hash: str, lookback_limit: int = 1000) -> dict:
        """
        Lookup an invoice by its r_hash

        Args:
            r_hash (str): r_hash to look up
            lookback_limit (int, optional): Maximum number of invoices to check.
                Defaults to 1000.

        Returns:
            dict: Invoice details found
        """
        self.refresh_invoices(lookback_limit)

        res = self.invoice_lookup.get(r_hash, None)

        return res

    @_check_login
    def correct_rhash(self, invoice_data: dict):

        invoice_data["r_hash"] = (
            base64.b64encode(bytes(invoice_data["r_hash"]["data"]))
        ).decode("utf-8")

        return invoice_data

    @_check_login
    def balance(self) -> int:
        """
        Get the current ballance of BTC in the walled of the logged
        in user.

        Returns:
            int: Value amount in the wallet
        """
        res = self.http.get(
            f"{ROOT_URL}/balance",
            headers={"Authorization": f"{self.access_token}"},
        )

        self._check_limit_reached(res.headers)
        res.raise_for_status()
        res_dict = res.json()
        return res_dict.get("BTC", {"AvailableBalance": 0}).get("AvailableBalance", 0)

    @_check_login
    def get_on_chain_address(self) -> str:
        """
        Get the on chain address for the wallet of the logged in user

        Returns:
            str: On-chain address
        """
        res = self.http.get(
            f"{ROOT_URL}/getbtc",
            headers={"Authorization": f"{self.access_token}"},
        )

        self._check_limit_reached(res.headers)
        res.raise_for_status()
        res_dict = res.json()
        return res_dict[0]["address"]

    @_check_login
    def get_node_info(self) -> dict:
        """
        Get details of the Blue wallet lightning node

        Returns:
            dict: Information on the lightning node
        """
        res = self.http.get(
            f"{ROOT_URL}/getinfo",
            headers={"Authorization": f"{self.access_token}"},
        )

        self._check_limit_reached(res.headers)
        res.raise_for_status()
        res_dict = res.json()
        return res_dict
