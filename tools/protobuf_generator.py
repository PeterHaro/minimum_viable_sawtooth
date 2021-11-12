#! /usr/bin/env python3
import os
import re
import tempfile
from glob import glob
from os.path import dirname

from grpc_tools.protoc import main as _protoc

TOP_DIR = dirname(dirname(__file__))
SRC_DIR = os.path.join(TOP_DIR, 'protos')


def make_protobuf(path, pkg_name):
    output_directory = os.path.join(TOP_DIR, path, pkg_name)
    os.makedirs(output_directory, exist_ok=True)

    init_py = os.path.join(output_directory, '__init__.py')

    if not os.path.exists(init_py):
        with open(init_py, mode='w'):
            pass

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_pkg_dir = os.path.join(tmp_dir, pkg_name)
        os.makedirs(tmp_pkg_dir)

        cwd = os.getcwd()
        os.chdir(SRC_DIR)
        proto_files = glob("*.proto")
        os.chdir(cwd)

        for proto in proto_files:
            src = os.path.join(SRC_DIR, proto)
            dst = os.path.join(tmp_pkg_dir, proto)
            with open(src, encoding='utf-8') as fin:
                with open(dst, "w", encoding='utf-8') as fout:
                    src_contents = fin.read()
                    fixed_contents = fix_import(src_contents, pkg_name)
                    fout.write(fixed_contents)

        _protoc([
                    __file__,
                    "-I=%s" % tmp_dir,
                    "--python_out=%s" % os.path.join(TOP_DIR, path),
                ] + glob("%s/*.proto" % tmp_pkg_dir))
        print("Generated protobuf classes: {}".format(output_directory))


def fix_import(contents, pkg, sub_dir=False):
    pattern = r'^import "(.*)\.proto\"'
    if sub_dir:
        template = r'import "%s/\1_pb2/\1.proto"'
    else:
        template = r'import "%s/\1.proto"'

    return re.sub(
        pattern,
        lambda match: match.expand(template) % pkg,
        contents,
        flags=re.MULTILINE
    )


if __name__ == '__main__':
    make_protobuf('processors/supply_chain_transaction_processors', 'protobuf')
   # make_protobuf('ledger_sync', ' node/protobuf')
   # make_protobuf('ledger_sync', ' python/protobuf')
    make_protobuf('tests', 'integration_tests/protobuf')
