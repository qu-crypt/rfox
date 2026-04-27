"""argparse dispatcher for rfox. main() is the entry point."""
import argparse
import sys

from . import commands


def build_parser():
    p = argparse.ArgumentParser(
        prog="rfox",
        description="Unified rfcat helper. Run with no args for an interactive menu.",
    )
    sub = p.add_subparsers(dest="cmd")
    for name, mod in commands.ALL:
        cp = sub.add_parser(name, help=getattr(mod, "HELP", ""))
        mod.add_args(cp)
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.cmd:
        # No subcommand -> interactive menu
        from . import menu
        return menu.main_menu(parser)

    mod = commands.get(args.cmd)
    return mod.run(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
