"""
Inspired from: https://github.com/zeromq/pyzmq/issues/1241#issuecomment-441187527
TODO: replace with more efficient shared-memory solution
"""
import zmq
import threading

ctx = zmq.Context()
_zmq_port = {}
_zmq_lock = threading.Lock()

def init_publisher(pipe_id, buffer_size=1024 * 1024):
    """
    pipe_id is for multi-camera support
    """
    global _zmq_port, _zmq_pub
    with _zmq_lock:
        pub = ctx.socket(zmq.PUB)
        pub.setsockopt(zmq.SNDHWM, 2)
        pub.setsockopt(zmq.SNDBUF, 2*buffer_size)  # see: http://api.zeromq.org/4-2:zmq-setsockopt
        _zmq_port[pipe_id] = pub.bind_to_random_port('tcp://127.0.0.1')

    zeros = bytes(buffer_size)
    def send(data):
        pub.send(data, zmq.SNDMORE)
        pub.send(zeros)

    return send

def init_subscriber(pipe_id, buffer_size=1024 * 1024):
    """
    pipe_id is for multi-camera support
    """
    with _zmq_lock:
        port = _zmq_port.get(pipe_id, None)
        if port is None:
            return None
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.SUBSCRIBE, b'')  # '' is topic
    sub.setsockopt(zmq.RCVHWM, 2)
    sub.setsockopt(zmq.RCVBUF, 2*buffer_size)
    sub.connect(f'tcp://127.0.0.1:{port}')

    def receive():
        data, _ = sub.recv_multipart()
        return data

    return receive
