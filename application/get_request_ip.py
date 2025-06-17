from flask import request


def get_request_ip():
    """
    Get the IP address of the requester. Not always accurate: the proxy is not currently set up to
    strip the request headers before passing them along, so very easy to spoof (but better n nothin)
    """
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr
