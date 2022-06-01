user_service_port = 50051
# Node IP lookup table
node_ip_lut = {
    0: {"ip_addr": "172.16.238.2", "port": "50050"},
    1: {"ip_addr": "172.16.238.3", "port": "50050"},
    2: {"ip_addr": "172.16.238.4", "port": "50050"},
    3: {"ip_addr": "172.16.238.5", "port": "50050"},
    4: {"ip_addr": "172.16.238.6", "port": "50050"},
    5: {"ip_addr": "172.16.238.7", "port": "50050"},
    6: {"ip_addr": "172.16.238.8", "port": "50050"},
    7: {"ip_addr": "172.16.238.9", "port": "50050"},
    8: {"ip_addr": "172.16.238.10", "port": "50050"},
    9: {"ip_addr": "172.16.238.11", "port": "50050"},
    10: {"ip_addr": "172.16.238.12", "port": "50050"},
    11: {"ip_addr": "172.16.238.13", "port": "50050"},
}
total_server = 4
fault_server = 1
server_id = 1
batch_size = 1
block_path_header = f'/usr/local/src/hbbft-wallet/test/blocks/block_file_'
block_path = f'{block_path_header}{server_id}'
