from setuptools import setup

setup(
    name='hbbft',
    version='0.1',
    packages=['hbbft', 'hbbft.client', 'hbbft.common', 'hbbft.common.protos',
              'hbbft.server', 'hbbft.server.UserServiceHandler', 'hbbft.server.BackendServiceHandler',
              'hbbft.server.HoneyBadgerBFT-Python', 'hbbft.server.HoneyBadgerBFT-Python.docs',
              'hbbft.server.HoneyBadgerBFT-Python.misc', 'hbbft.server.HoneyBadgerBFT-Python.misc.shoup_tsig',
              'hbbft.server.HoneyBadgerBFT-Python.test', 'hbbft.server.HoneyBadgerBFT-Python.test.crypto',
              'hbbft.server.HoneyBadgerBFT-Python.test.crypto.ecdsa',
              'hbbft.server.HoneyBadgerBFT-Python.test.crypto.threshenc',
              'hbbft.server.HoneyBadgerBFT-Python.test.crypto.threshsig',
              'hbbft.server.HoneyBadgerBFT-Python.experiments', 'hbbft.server.HoneyBadgerBFT-Python.experiments.ec2',
              'hbbft.server.HoneyBadgerBFT-Python.experiments.plots',
              'hbbft.server.HoneyBadgerBFT-Python.experiments.benchmark',
              'hbbft.server.HoneyBadgerBFT-Python.honeybadgerbft',
              'hbbft.server.HoneyBadgerBFT-Python.honeybadgerbft.core',
              'hbbft.server.HoneyBadgerBFT-Python.honeybadgerbft.crypto',
              'hbbft.server.HoneyBadgerBFT-Python.honeybadgerbft.crypto.ecdsa',
              'hbbft.server.HoneyBadgerBFT-Python.honeybadgerbft.crypto.threshenc',
              'hbbft.server.HoneyBadgerBFT-Python.honeybadgerbft.crypto.threshsig'],
    url='',
    license='',
    author='Jeffrey Xiong, Carl Zhang, Zhouyi Huang, Rui',
    author_email='',
    description=''
)
