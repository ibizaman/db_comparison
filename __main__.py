"""
Test performance of multiple databases
"""
import argparse
import postgres
from monitor import MonitorAction
import result_server


ACTIONS = [cls for cls in vars()['MonitorAction'].__subclasses__()]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers()
    for action_config in ACTIONS:
        name = action_config.__name__.lower()
        doc = "Test the {db} database".format(db=name)
        action_parser = subparsers.add_parser(name, help=doc, description=doc)
        action_config.add_subparser(action_parser)

    args = vars(parser.parse_args())
    func = args.pop('func')
    func(**args)

if __name__ == '__main__':
    main()

