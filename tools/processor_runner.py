#! /usr/bin/env python3
import os
import sys

TOP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

sys.path.insert(0, os.path.join(TOP_DIR, 'addressing'))
sys.path.insert(0, os.path.join(TOP_DIR, 'processors'))
sys.path.insert(0, os.path.join(TOP_DIR, 'protobuf'))

from processors.supply_chain_trainsaction_processors.main import main

if __name__ == '__main__':
    main()
