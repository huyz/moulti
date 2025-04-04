# ruff: noqa: E501 Line too long
import os
import sys
import json
from argparse import ArgumentParser, BooleanOptionalAction, _SubParsersAction
from pathlib import Path
from typing import Generator
import argcomplete
from . import __version__ as moulti_version
from .client import current_instance, moulti_socket_path, send_to_moulti, send_to_moulti_and_handle_reply, pipeline
from .environ import env, pint, float_str
from .widgets.cli import add_cli_arguments
from .manpage import manpage_parse, manpage_run

def init(args: dict) -> None:
	"""Start a new Moulti instance."""

	from .app import main as init_moulti # pylint: disable=import-outside-toplevel
	init_moulti(**args)

def moulti_run_should_suffix_instance_name(args: dict) -> bool:
	"""
	By default, `moulti run` suffixes the instance name with the process id.
	Since the socket path is derived from the instance name, this helps prevent clashes and thus
	"cannot listen" errors.
	"""
	if env('MOULTI_SOCKET_PATH'):
		# If a socket path was explicitly set, then the instance name cannot affect
		# its computation. Therefore, there is no need to suffix the instance name.
		return False
	if args['no_suffix']:
		return False
	if env('MOULTI_RUN_NO_SUFFIX') is not None:
		return False
	return True

def run(args: dict) -> None:
	"""Start a new Moulti instance and run the given command."""
	if moulti_run_should_suffix_instance_name(args):
		os.environ['MOULTI_INSTANCE'] = f'{current_instance()}-{os.getpid()}'

	# Handle --print-env:
	if args['print_env']:
		from .app import run_environment # pylint: disable=import-outside-toplevel
		environment_variables = run_environment(args['command'], moulti_socket_path(), False)
		for name, value in environment_variables.items():
			print(f'{name}={value}')
		sys.exit(0)

	from .app import main as init_moulti # pylint: disable=import-outside-toplevel
	init_moulti(args['command'])

def wait(verbose: bool = False, delay: int = 500, max_attempts: int = 0) -> None:
	"""Wait until the Moulti instance is available.
	Args:
		verbose: if True, output the reason why each connection attempt failed
		delay: number of milliseconds between two connection attempts
		max_attempts: maximum number of attempts before giving up; 0 means "never give up"
	"""
	import time # pylint: disable=import-outside-toplevel
	connected = False
	attempts = 0
	while not connected:
		try:
			attempts += 1
			send_to_moulti({'command': 'ping'})
			connected = True
			break
		except Exception as exc:
			if verbose:
				print(f'Connection #{attempts} to {moulti_socket_path()}: {exc}')
			if max_attempts > 0 and attempts == max_attempts:
				print('Giving up.')
				break
			time.sleep(delay / 1000.0)
	sys.exit(0 if connected else 1)

def saved_files(directory: Path) -> Generator:
	"""
	Iterate over a directory supposedly generated by Moulti's "Save" feature.
	Yield pipeline()-compatible triplets.
	"""
	json_ext = '.properties.json'
	for json_file in sorted(directory.glob('*' + json_ext)):
		if not json_file.is_file():
			continue
		with json_file.open(encoding='utf-8', errors='surrogateescape') as json_file_desc:
			data = json.load(json_file_desc)
			log_file = json_file.with_name(json_file.name[:-len(json_ext)] + '.contents.log')
			fileno = os.open(str(log_file), os.O_RDONLY) if log_file.is_file() else None
			yield data.get('id'), data, fileno

def load(args: dict, read_size: int = 1024**2) -> None:
	"""
	Load the contents of a directory supposedly generated by Moulti's "Save" feature and push it to a Moulti instance.
	"""
	errors = pipeline(saved_files(args['saved_directory']), read_size)
	sys.exit(errors)

def diff_parse(args: dict) -> None:
	from .diff import diff_parse as real_diff_parse # pylint: disable=import-outside-toplevel
	real_diff_parse(args)

def diff_run(args: dict) -> None:
	from .diff import diff_run as real_diff_run # pylint: disable=import-outside-toplevel
	real_diff_run(args)

def add_main_commands(subparsers: _SubParsersAction) -> None:
	# moulti init
	init_parser = subparsers.add_parser('init', help='start a new Moulti instance')
	init_parser.set_defaults(func=init)

	# moulti run
	run_parser = subparsers.add_parser('run', help='start a new Moulti instance and run a command')
	run_parser.set_defaults(func=run)
	run_parser.add_argument('--print-env', action='store_true', default=False, help='print environment variables set by Moulti and exit')
	run_parser.add_argument('--no-suffix', '-n', action='store_true', default=False, help='do not suffix the instance name with the process id')
	run_parser.add_argument('command', type=str, nargs='+', help='command to run along with its arguments')

	# moulti wait
	wait_parser = subparsers.add_parser('wait', help='wait until the Moulti instance is available')
	wait_parser.set_defaults(func=wait)
	wait_parser.add_argument('--verbose', '-v', action='store_true', help='if True, output the reason why each connection attempt failed')
	wait_parser.add_argument('--delay', '-d', type=pint, default=500, help='number of milliseconds between two connection attempts')
	wait_parser.add_argument('--max-attempts', '-m', type=pint, default=0, help='maximum number of attempts before giving up; 0 means "never give up"')

	# moulti set
	set_parser = subparsers.add_parser('set', help='set Moulti options')
	set_parser.set_defaults(func=send_to_moulti_and_handle_reply, command='set')
	set_parser.add_argument('--title', '-t', default=None, type=str, help='title displayed at the top of the screen')
	set_parser.add_argument('--step-position', default=None, type=str, choices=('top', 'bottom'), help='whether to display steps at the top (default) or bottom of the screen')
	set_parser.add_argument('--step-direction', default=None, type=str, choices=('up', 'down'), help='whether to lay out steps up or down (default)')
	set_parser.add_argument('--progress-bar', default=None, action=BooleanOptionalAction, help='whether to display the progress bar')
	set_parser.add_argument('--progress-target', '-pt', default=None, type=float, help='total number of steps associated with the progress bar')
	set_parser.add_argument('--progress', '-p', default=None, type=float_str, help='progress so far, in number of steps; accept absolute or relative values, e.g. 50, +1 or -5')

	# moulti load
	load_parser = subparsers.add_parser('load', help='load a saved directory into Moulti')
	load_parser.set_defaults(func=load, command='load')
	arg = load_parser.add_argument('saved_directory', type=Path, help='path to a directory generated by Moulti\'s "Save" feature')
	arg.completer = argcomplete.completers.DirectoriesCompleter()

	# moulti diff parse/run
	diff_parser = subparsers.add_parser('diff', help='load unified diff data into Moulti')
	diff_subparsers = diff_parser.add_subparsers(required=True)
	diff_parse_parser = diff_subparsers.add_parser('parse', help='load unified diff data into Moulti from a file')
	diff_parse_parser.set_defaults(func=diff_parse)
	arg = diff_parse_parser.add_argument('diff_filepath', type=Path, help='path to a unified diff file')
	arg.completer = argcomplete.completers.FilesCompleter()
	diff_run_parser = diff_subparsers.add_parser('run', help='load unified diff data into Moulti from a command')
	diff_run_parser.set_defaults(func=diff_run)
	diff_run_parser.add_argument('command', type=str, nargs='+', help='command to run along with its arguments')

	# moulti manpage parse/run
	manpage_parser = subparsers.add_parser('manpage', help='load man page data into Moulti')
	manpage_subparsers = manpage_parser.add_subparsers(required=True)
	manpage_parse_parser = manpage_subparsers.add_parser('parse', help='load man page data into Moulti from a file')
	manpage_parse_parser.set_defaults(func=manpage_parse)
	arg = manpage_parse_parser.add_argument('manpage_filepath', type=Path, help='path to a file holding man output')
	arg.completer = argcomplete.completers.FilesCompleter()
	manpage_run_parser = manpage_subparsers.add_parser('run', help='load man page data into Moulti from a command')
	manpage_run_parser.set_defaults(func=manpage_run)
	manpage_run_parser.add_argument('command', type=str, nargs='+', help='command to run along with its arguments')

	# moulti scroll
	scroll_parser = subparsers.add_parser('scroll', help='scroll to make a specific step visible')
	scroll_parser.set_defaults(func=send_to_moulti_and_handle_reply, command='scroll')
	scroll_parser.add_argument('id', type=str, help='step identifier')
	scroll_parser.add_argument('offset', type=int, nargs='?', default=None, help='-1: last line, 0: first line, 1: second line, etc.')

def build_arg_parser() -> ArgumentParser:
	arg_parser = ArgumentParser(prog='moulti', description='step-by-step logs')
	arg_parser.add_argument('--version', action='version', version=moulti_version)
	subparsers = arg_parser.add_subparsers(required=True)
	# moulti init, moulti wait:
	add_main_commands(subparsers)
	# moulti <widget>:
	add_cli_arguments(subparsers)
	return arg_parser

def first_non_option_argument(args: list[str], start: int = 0) -> int|None:
	"""
	Return the index of the first non-option argument, i.e. the first argument that does not start with a "-" (dash)
	character.
	"""
	for index, arg in enumerate(args[start:], start):
		if not arg.startswith('-'):
			return index
	return None

def inject_double_dash_before_command(args: list[str], start: int = 0) -> None:
	"""
	Inject "--" right before the first non-option argument.
	"""
	index = first_non_option_argument(args, start)
	if index is not None and index > 0 and args[index - 1] != '--':
		args.insert(index, '--')

def adjust_cli_args(args: list[str]) -> None:
	"""
	Command-line arguments are parsed using argparse. Consequently, "run" subcommands often require users to add "--" to
	their command line, e.g. "moulti run -- ls -al" instead of "moulti run ls -al".
	Detect such cases and inject "--" if it is missing.
	"""
	if len(args) < 2:
		return
	if args[1] == 'run':
		inject_double_dash_before_command(args, 2)
	elif args[1] in ('manpage', 'diff') and args[2] == 'run':
		inject_double_dash_before_command(args, 3)

def main() -> None:
	try:
		arg_parser = build_arg_parser()
		argcomplete.autocomplete(arg_parser, always_complete_options='long')
		adjust_cli_args(sys.argv)
		args = vars(arg_parser.parse_args())
		func = args.pop('func')
		# Subtlety: func and args are not always used the same way:
		if func == wait: # pylint: disable=comparison-with-callable
			wait(**args)
		else:
			func(args)
	except KeyboardInterrupt:
		print('')
		sys.exit(1)

if __name__ == '__main__':
	main()
