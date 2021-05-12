import pytest


@pytest.fixture(scope="session")
def find_free_port():
    """
    https://gist.github.com/bertjwregeer/0be94ced48383a42e70c3d9fff1f4ad0
    """

    def _find_free_port():
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", 0))
        portnum = s.getsockname()[1]
        s.close()

        return portnum

    return _find_free_port
