import argparse
import sys
from pathlib import Path

from .commands.config import (
    cmd_config_dir,
    cmd_config_path,
    cmd_config_show,
    cmd_config_tkn,
)
from .commands.prep import cmd_prep

TOP_OPTIONS = ["-h", "--help"]


def add_default_command(argv, commands):
    if not argv:  # nothing typed: let argparse say a command is required
        return argv
    if argv[0] in commands:  # already a command
        return argv
    if argv[0] in TOP_OPTIONS:  # an option like --help, not a video
        return argv
    return ["prep"] + argv


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]  # a real run: everything after the script name

    parser = argparse.ArgumentParser(
        prog="jarr", description="The CLI Jellyfin companion tool."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prep", help="Rename file into recommended format.")
    prep.add_argument("file", type=Path, help="File to be formatted.")
    prep.add_argument(
        "destination_dir",
        type=Path,
        nargs="?",
        help="Where the processed file will land. (Leave empty for default)",
    )
    prep.add_argument(
        "-c",
        "--copy",
        action="store_true",
        help="Instead of moving, copy the file to the destination.",
    )
    prep.set_defaults(func=cmd_prep)

    config = sub.add_parser("config", help="Change the configuration file.")
    config_sub = config.add_subparsers(dest="subcommand", required=True)

    config_tkn = config_sub.add_parser("token", help="Change or set your TMDB token.")
    config_tkn.set_defaults(func=cmd_config_tkn)

    config_dir = config_sub.add_parser(
        "dir", help="Change or set the default directory."
    )
    config_dir.add_argument("new_dir", type=Path, help="Directory to be saved.")
    config_dir.set_defaults(func=cmd_config_dir)

    config_show = config_sub.add_parser("show", help="Show current settings.")
    config_show.set_defaults(func=cmd_config_show)

    config_path = config_sub.add_parser("path", help="Show the path of the config file")
    config_path.set_defaults(func=cmd_config_path)

    argv = add_default_command(argv, sub.choices)

    args = parser.parse_args(argv)
    return args
