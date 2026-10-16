"""Start a hidden child without inheriting PowerShell's HTTP response pipes."""
import argparse
import subprocess


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--stdout', required=True)
    parser.add_argument('--stderr', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    with open(args.stdout, 'wb') as output, open(args.stderr, 'wb') as error:
        child = subprocess.Popen(command, cwd=args.cwd, stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=error, close_fds=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
    print(child.pid)
