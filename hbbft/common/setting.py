user_service_port = 50051
# Node IP lookup table
node_ip_lut = {
    0: {"ip_addr": "172.16.238.2", "port": "50050"},
    1: {"ip_addr": "172.16.238.3", "port": "50050"},
    2: {"ip_addr": "172.16.238.4", "port": "50050"},
    3: {"ip_addr": "172.16.238.5", "port": "50050"},
}
total_server = 4
fault_server = 1
server_id = 1
batch_size = 1
block_path = f'/usr/local/src/hbbft-wallet/test/blocks/block_file_{server_id}'
