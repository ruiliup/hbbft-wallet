import os
import sys
import subprocess
import re
import fnmatch
import pkg_resources

# Test necessary dependencies
try:
    from grpc_tools import protoc
except ImportError:
    raise Exception(
        "grpc_tools must been installed before calling this generate script"
        "Use python3 -m pip install grpcio-tools to insall this package"
    )

def get_parent_dir(child_dir, recursion_lvl=1):
    if recursion_lvl == 1:
        return os.path.join(child_dir, os.pardir)
    else:
        return get_parent_dir(
            os.path.join(child_dir, os.pardir), recursion_lvl=recursion_lvl - 1
        )


# Location of .proto files
GRPC_TOOL_DIR = os.path.realpath(os.path.dirname(__file__))
print(GRPC_TOOL_DIR)
PROTO_DIR = os.path.join(get_parent_dir(GRPC_TOOL_DIR, recursion_lvl=1), "protos")
print(PROTO_DIR)
# Use regular expression to filter .proto files
PB_EXT_REGEX_OBJ = re.compile(fnmatch.translate("*.proto"))
PROTO_FILES = [
    protofile
    for protofile in os.listdir(PROTO_DIR)
    if PB_EXT_REGEX_OBJ.match(protofile) is not None
]
print(PROTO_FILES)

if __name__ == "__main__":
    # Create directory in radar_comm called 'generated' to hold compiled protobuf modules, fine if dir exists already
    subprocess.call(["mkdir", "-p", "generated"], cwd=GRPC_TOOL_DIR)
    gen_path = os.path.join(GRPC_TOOL_DIR, "generated")

    # Compile each protobuf needed for interfacing with radar
    for protofile in PROTO_FILES:
        subprocess.call(
            [
                "python3",
                "-m",
                "grpc_tools.protoc",
                "-I" + PROTO_DIR,
                "--python_out",
                gen_path,
                "--grpc_python_out",
                gen_path,
                protofile,
            ],
            cwd=PROTO_DIR,
        )
