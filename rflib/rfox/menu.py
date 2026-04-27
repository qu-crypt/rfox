"""Interactive menu shim - thin wrapper that drives argparse.

For each command:
  1. show its arg list with defaults
  2. prompt the user for each arg (Enter to keep default)
  3. call the same dispatcher the CLI uses
"""
import argparse
import shlex
import sys

from . import commands


BANNER = r"""
       __           
 _ __ / _| _____  __
| '__| |_ / _ \ \/ /
| |  |  _| (_) >  < 
|_|  |_|  \___/_/\_\

rfox
    unified rfcat helper.  type 'q' at any prompt to quit.
"""


def _ask(prompt, default=None):
    if default is not None and default != "":
        s = input(f"{prompt} [{default}]: ")
    else:
        s = input(f"{prompt}: ")
    if s.strip().lower() == "q":
        raise KeyboardInterrupt
    return s.strip() or (default if default is not None else "")


def _print_menu():
    print()
    print("Commands:")
    for i, (name, mod) in enumerate(commands.ALL, 1):
        help_text = getattr(mod, "HELP", "")
        print(f"  {i:>2}. {name:<14} {help_text}")
    print(f"   q. quit")
    print()


def _prompt_and_run(parser, name):
    """Use the command's prompt() to fill an args object, then run it."""
    sub_parsers_action = next(
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    sub = sub_parsers_action.choices[name]

    # Build a default Namespace from the subparser
    args = sub.parse_args([])
    args.cmd = name

    mod = commands.get(name)
    try:
        if hasattr(mod, "prompt"):
            mod.prompt(args)
    except KeyboardInterrupt:
        print()
        return None

    print()
    print("# running:", name, _format_args(args))
    print()
    try:
        return mod.run(args) or 0
    except KeyboardInterrupt:
        print("\n# interrupted.")
        return 130
    except Exception as e:
        print(f"# error: {e}", file=sys.stderr)
        return 1


def _format_args(args):
    """Display args in CLI form so the user can copy-paste them later."""
    parts = []
    skip = {"cmd", "action", "debug"}
    for k, v in sorted(vars(args).items()):
        if k in skip or v is None or v is False:
            continue
        if v is True:
            parts.append(f"--{k.replace('_', '-')}")
        else:
            parts.append(f"--{k.replace('_', '-')} {shlex.quote(str(v))}")
    return " ".join(parts)


def main_menu(parser):
    print(BANNER)
    while True:
        _print_menu()
        try:
            choice = input("choose: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if choice in ("q", "quit", "exit", ""):
            return 0
        # accept either index or name
        target = None
        if choice.isdigit():
            i = int(choice) - 1
            if 0 <= i < len(commands.ALL):
                target = commands.ALL[i][0]
        else:
            for name, _ in commands.ALL:
                if name == choice:
                    target = name
                    break
        if not target:
            print(f"  ? unknown choice: {choice!r}")
            continue
        _prompt_and_run(parser, target)
        print()
        cont = input("press Enter for menu, q to quit: ").strip().lower()
        if cont == "q":
            return 0
