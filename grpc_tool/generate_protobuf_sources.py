import os
import subprocess
import re
import fnmatch


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
root = get_parent_dir(GRPC_TOOL_DIR, recursion_lvl=1)
PROTO_DIR = os.path.join(root, "hbbft/common/protos")
PROTO_DIR = os.path.abspath(PROTO_DIR)
print(PROTO_DIR)
# # Use regular expression to filter .proto files
PB_EXT_REGEX_OBJ = re.compile(fnmatch.translate("*.proto"))
PROTO_FILES = [
    protofile
    for protofile in os.listdir(PROTO_DIR)
    if PB_EXT_REGEX_OBJ.match(protofile) is not None
]
print(PROTO_FILES)

if __name__ == "__main__":
    for p in PROTO_FILES:
        cmd = [
            "python3",
            "-m",
            "grpc_tools.protoc",
            "-I.",
            f"hbbft/common/protos/{p}",
            "--python_out",
            ".",
            "--grpc_python_out",
            "."
        ]
        print(' '.join(cmd))
        subprocess.call(
            cmd,
            cwd=root,
        )
