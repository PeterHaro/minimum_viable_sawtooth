import argparse
import os
import sys

import pkg_resources
from sawtooth_sdk.processor.config import get_log_config
from sawtooth_sdk.processor.config import get_log_dir
from sawtooth_sdk.processor.core import TransactionProcessor
from sawtooth_sdk.processor.log import init_console_logging
from sawtooth_sdk.processor.log import log_configuration

from processor.paasforchain_supply_chain_processor.configuration import ENDPOINT
from processor.paasforchain_supply_chain_processor.handler import SupplyChainHandler

DISTRIBUTION_NAME = 'paasforchain-supply-chain'


def create_parser(prog_name, args):
    parser = argparse.ArgumentParser(prog=prog_name, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('endpoint',
                        nargs='?',
                        default=ENDPOINT,
                        help='Endpoint for the validator connection')

    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Increase output sent to stderr')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}').format(version),
        help='print version information')

    return parser.parse_args(args)


def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name, args)
    processor = None
    try:
        processor = TransactionProcessor(url=args.endpoint)
        log_config = get_log_config(filename="paasforchain_log_config.toml")
        if log_config is None:
            log_config = get_log_config(filename="paasforchain_log_config.yaml")

        if log_config is not None:
            log_configuration(log_config=log_config)
        else:
            log_dir = get_log_dir()
            # use the transaction processor zmq identity for filename
            log_configuration(
                log_dir=log_dir,
                name="marketplace-" + str(processor.zmq_id)[2:-1])
        init_console_logging(verbose_level=parser.verbose)
        handler = SupplyChainHandler()
        processor.add_handler(handler)
        processor.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Error: {}".format(e), file=sys.stderr)
    finally:
        processor.stop()
