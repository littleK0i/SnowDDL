from argparse import ArgumentParser, HelpFormatter
from logging import getLogger, StreamHandler, Formatter
from os import environ, getcwd
from pathlib import Path
from re import compile

from snowddl.fernet.wrapper import FernetWrapper


def init_logger():
    logger = getLogger("snowddl")
    logger.setLevel("INFO")

    formatter = Formatter("%(asctime)s - %(levelname)s - %(message)s")
    formatter.default_msec_format = "%s.%03d"

    handler = StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def entry_point():
    parser = build_parser()
    args = vars(parser.parse_args())
    wrapper = FernetWrapper(args.get("k"))

    if args["action"] == "generate-key":
        action_generate_key(args, wrapper)
    elif args["action"] == "encrypt":
        action_encrypt(args, wrapper)
    elif args["action"] == "decrypt":
        action_decrypt(args, wrapper)
    elif args["action"] == "rotate":
        action_rotate(args, wrapper)
    elif args["action"] == "config-encrypt":
        action_config_encrypt(args, wrapper)
    elif args["action"] == "config-decrypt":
        action_config_decrypt(args, wrapper)
    elif args["action"] == "config-rotate":
        action_config_rotate(args, wrapper)


def build_parser():
    formatter = lambda prog: HelpFormatter(prog, max_help_position=32)

    parser = ArgumentParser(
        prog="snowddl-fernet",
        description="Utility functions to encrypt secrets for SnowDDL config with Fernet",
        formatter_class=formatter,
    )

    subparsers = parser.add_subparsers(dest="action")
    subparsers.required = True

    # Action: generate-key
    generate_key_subparser = subparsers.add_parser("generate-key", help="Generate a fresh encryption key")

    generate_key_subparser.add_argument(
        "-k",
        help="All current encryption keys separated by comma (<key1>,<key2>,<key3>)",
        metavar="ENCRYPTION_KEYS",
        default=environ.get(FernetWrapper.ENV_ENCRYPTION_KEYS),
    )

    generate_key_subparser.add_argument(
        "--prepend",
        help="Prepend newly generated key to existing keys",
        default=False,
        action="store_true",
    )

    generate_key_subparser.add_argument(
        "--export",
        help="Output key(s) as export env command for CLI",
        default=False,
        action="store_true",
    )

    # Action: encrypt
    encrypt_subparser = subparsers.add_parser("encrypt", help="Encrypt value with first key")

    encrypt_subparser.add_argument(
        "-k",
        help="All current encryption keys separated by comma (<key1>,<key2>,<key3>)",
        metavar="ENCRYPTION_KEYS",
        default=environ.get(FernetWrapper.ENV_ENCRYPTION_KEYS),
    )

    encrypt_subparser.add_argument(
        "value",
        help="String value",
        metavar="VALUE",
    )

    # Action: decrypt
    decrypt_subparser = subparsers.add_parser("decrypt", help="Decrypt value with any key")

    decrypt_subparser.add_argument(
        "-k",
        help="All current encryption keys separated by comma (<key1>,<key2>,<key3>)",
        metavar="ENCRYPTION_KEYS",
        default=environ.get(FernetWrapper.ENV_ENCRYPTION_KEYS),
    )

    decrypt_subparser.add_argument(
        "value",
        help="Encrypted value",
        metavar="VALUE",
    )

    # Action: rotate
    rotate_subparser = subparsers.add_parser("rotate", help="Rotate value encrypted with any key")

    rotate_subparser.add_argument(
        "-k",
        help="All current encryption keys separated by comma (<key1>,<key2>,<key3>)",
        metavar="ENCRYPTION_KEYS",
        default=environ.get(FernetWrapper.ENV_ENCRYPTION_KEYS),
    )

    rotate_subparser.add_argument(
        "value",
        help="Encrypted value to rotate",
        metavar="VALUE",
    )

    # Action: config-encrypt
    config_encrypt_subparser = subparsers.add_parser("config-encrypt", help="Encrypy all values in config")

    config_encrypt_subparser.add_argument(
        "-k",
        help="All current encryption keys separated by comma (<key1>,<key2>,<key3>)",
        metavar="ENCRYPTION_KEYS",
        default=environ.get(FernetWrapper.ENV_ENCRYPTION_KEYS),
    )

    config_encrypt_subparser.add_argument(
        "-c",
        help="Path to config directory (default: current directory)",
        metavar="CONFIG_PATH",
        default=getcwd(),
    )

    # Action: config-decrypt
    config_decrypt_subparser = subparsers.add_parser("config-decrypt", help="Decrypt all values in config")

    config_decrypt_subparser.add_argument(
        "-k",
        help="All current encryption keys separated by comma (<key1>,<key2>,<key3>)",
        metavar="ENCRYPTION_KEYS",
        default=environ.get(FernetWrapper.ENV_ENCRYPTION_KEYS),
    )

    config_decrypt_subparser.add_argument(
        "-c",
        help="Path to config directory (default: current directory)",
        metavar="CONFIG_PATH",
        default=getcwd(),
    )

    # Action: config-rotate
    config_rotate_subparser = subparsers.add_parser("config-rotate", help="Rotate all values in config")

    config_rotate_subparser.add_argument(
        "-k",
        help="All current encryption keys separated by comma (<key1>,<key2>,<key3>)",
        metavar="ENCRYPTION_KEYS",
        default=environ.get(FernetWrapper.ENV_ENCRYPTION_KEYS),
    )

    config_rotate_subparser.add_argument(
        "-c",
        help="Path to config directory (default: current directory)",
        metavar="CONFIG_PATH",
        default=getcwd(),
    )

    return parser


def action_generate_key(args, wrapper: FernetWrapper):
    all_keys = [wrapper.generate_key()]

    if args.get("prepend"):
        all_keys.extend(wrapper.key_sequence)

    if args.get("export"):
        print(f"export {wrapper.ENV_ENCRYPTION_KEYS}={','.join(all_keys)}")
    else:
        print(",".join(all_keys))


def action_encrypt(args, wrapper: FernetWrapper):
    print(wrapper.encrypt(args["value"]))


def action_decrypt(args, wrapper: FernetWrapper):
    print(wrapper.decrypt(args["value"]))


def action_rotate(args, wrapper: FernetWrapper):
    print(wrapper.rotate(args["value"]))


def action_config_encrypt(args, wrapper: FernetWrapper):
    logger = init_logger()
    regexp = compile(r"!encrypt\s+\"?(.+?)\"?\n")

    for file in get_config_files_generator(args):
        original_text = file.read_text(encoding="utf-8")
        updated_text, number_of_sub = regexp.subn(lambda m: f"!decrypt {wrapper.encrypt(m[1])}\n", original_text)

        if number_of_sub > 0:
            file.write_text(updated_text, encoding="utf-8")
            logger.info(f"Updated file [{file}] with [{number_of_sub}] substitutions")


def action_config_decrypt(args, wrapper: FernetWrapper):
    logger = init_logger()
    regexp = compile(r"!decrypt\s+\"?(.+?)\"?\n")

    for file in get_config_files_generator(args):
        original_text = file.read_text(encoding="utf-8")
        updated_text, number_of_sub = regexp.subn(lambda m: f'!encrypt "{wrapper.decrypt(m[1])}"\n', original_text)

        if number_of_sub > 0:
            file.write_text(updated_text, encoding="utf-8")
            logger.info(f"Updated file [{file}] with [{number_of_sub}] substitutions")


def action_config_rotate(args, wrapper: FernetWrapper):
    logger = init_logger()
    regexp = compile(r"!decrypt\s+\"?(.+?)\"?\n")

    for file in get_config_files_generator(args):
        original_text = file.read_text(encoding="utf-8")
        updated_text, number_of_sub = regexp.subn(lambda m: f"!decrypt {wrapper.rotate(m[1])}\n", original_text)

        if number_of_sub > 0:
            file.write_text(updated_text, encoding="utf-8")
            logger.info(f"Updated file [{file}] with [{number_of_sub}] substitutions")


def get_config_files_generator(args):
    path = Path(args["c"])

    if not path.is_dir():
        raise ValueError(f"Config path [{path}] is not a directory")

    for file in path.glob("**/*.yaml"):
        yield file
