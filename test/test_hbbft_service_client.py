from hbbft.common.setting import user_service_port, total_server, fault_server, server_id, batch_size
from hbbft.client.user_service_client import UserServiceClient
from honeybadgerbft.core.honeybadger import HoneyBadgerBFT
from honeybadgerbft.crypto.threshenc import tpke
from honeybadgerbft.crypto.threshsig.boldyreva import dealer
import random
import gevent
from gevent.queue import Queue


def simple_router(N, maxdelay=0.005, seed=None):
    """Builds a set of connected channels, with random delay

    :return: (receives, sends)
    """
    rnd = random.Random(seed)
    #if seed is not None: print 'ROUTER SEED: %f' % (seed,)

    queues = [Queue() for _ in range(N)]
    _threads = []

    def makeSend(i):
        def _send(j, o):
            delay = rnd.random() * maxdelay
            if not i % 3:
                delay *= 1000
            #delay = 0.1
            #print 'SEND   %8s [%2d -> %2d] %2.1f' % (o[0], i, j, delay*1000), o[1:]
            gevent.spawn_later(delay, queues[j].put_nowait, (i, o))
        return _send

    def makeRecv(j):
        def _recv():
            (i, o) = queues[j].get()
            #print 'RECV %8s [%2d -> %2d]' % (o[0], i, j)
            return (i, o)
        return _recv

    return ([makeSend(i) for i in range(N)],
            [makeRecv(j) for j in range(N)])


if __name__ == "__main__":
    sid = 'sidA'
    N = total_server
    f = fault_server
    seed = server_id  # Add a thread id/server id/process id
    rnd = random.Random(seed)
    router_seed = rnd.random()
    sends, recvs = simple_router(N, seed=router_seed)
    sPK, sSKs = dealer(N, f+1, seed=seed)
    # Generate threshold enc keys
    ePK, eSKs = tpke.dealer(N, f+1)
    hbbft = HoneyBadgerBFT(sid, server_id, batch_size, N, f,
                           sPK, sSKs[server_id-1], ePK, eSKs[server_id-1],
                           sends[server_id-1], recvs[server_id-1])
    hbbft.get_txn(user_service_port)
