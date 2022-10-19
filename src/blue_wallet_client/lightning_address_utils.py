import requests


def decode_lightning_address(lightning_address: str):
    """
    Parse the lightning address into domain and username

    Args:
        lightning_address (str): Bitcoin lightning address

    Returns:
        domain_url: domain
        username: usermane
    """

    str_separated = lightning_address.split("@")

    if len(str_separated) != 2:
        raise Exception(
            f"""The address has to include exactly one '@'. 
            Address supplied: '{lightning_address}' """
        )

    domain_url = str_separated[1]
    username = str_separated[0]

    return username, domain_url


def get_lightning_address_url(lightning_address: str) -> str:
    """
    Get LN url from the lightning address

    Args:
        lightning_address (str): Bitcoin lightning address

    Returns:
        url: LN url
    """

    username, domain_url = decode_lightning_address(lightning_address)

    url = f"https://{domain_url}/.well-known/lnurlp/{username}"

    return url


def call_server_url(lightning_address: str, amount: int) -> dict:
    """
    Make a call to LN url and obtain the return value. Then verify the
    returned data.

    Args:
        lightning_address (str): Lightning address to make the call for
        amount (int): Amount to send to the address in Satoshis

    Returns:
        dict: Returned data
    """
    url = get_lightning_address_url(lightning_address)
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
    except Exception as e:
        raise Exception(f"Unable to reach {url}, got error: {e}")

    if res.json().get("status", "") == "ERROR":
        raise Exception(
            f"Bad response from lightning address server: {res.get('reason', '')}"
        )

    processed_res = res.json()

    check_response(processed_res, amount)

    return processed_res


def check_response(data: dict, amount: int):
    """
    Check the response from LN url

    Args:
        data (str): Data returned from LN url
        amount (int): Amount to be sent

    """
    missing_fields = set(["minSendable", "maxSendable", "tag"]) - set(data.keys())

    if len(missing_fields) > 0:
        raise Exception(f"Response is missing the fields {missing_fields}")

    if data["minSendable"] > amount * 1000:
        raise Exception(
            f"""
            For this address, min sandable is {data['minSendable']} mili sat 
            that is more than our price per click of {amount*1000} mili sat
            """
        )

    if data["maxSendable"] < amount * 1000:
        raise Exception(
            f"""
            For this address, max sandable is {data['maxSendable']} mili sat 
            that is less than our price per click of {amount*1000} mili sat
            """
        )

    if data["tag"] != "payRequest":
        raise Exception(
            f"For this address, response is not a pay request, it is instead {data['tag']}."
        )


def get_invoice_from_address(
    lightning_address: str, amount: int, comment: str = None, nonce=None
) -> str:
    """
    Get an invoice from a lightning address

    Args:
        lightning_address (str): lightning address
        amount (int): Amount to send
        comment (str, optional): Comment to add into the invoice. Defaults to None.
        nonce (_type_, optional): Nonce of the request. Defaults to None.
    """
    res = call_server_url(lightning_address, amount)
    callback_url = res["callback"]

    callback_query_params = {}
    callback_query_params["amount"] = int(amount) * 1000

    if comment:
        callback_query_params["comment"] = comment

    if nonce:
        callback_query_params["nonce"] = nonce

    try:
        res = requests.get(callback_url, params=callback_query_params, timeout=5)
        res.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Unable to reach {callback_url} for get Lightning invoice, got error: {e}"
        )

    processed_res = (res.json())["pr"]

    return processed_res
