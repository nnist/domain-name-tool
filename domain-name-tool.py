# https://en.wikipedia.org/wiki/Domain_hack
# TODO unit tests

import datetime
import argparse
import sys
import os
import time
import subprocess

def check_domain(domain):
    """Do a whois request on domain. Return the domain's status."""
    try:
        process = subprocess.run(['whois', domain], timeout=1,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, check=True,
                                 universal_newlines=True)
        output = process.stdout
        if 'NOT AVAILABLE' in output or 'NOT ALLOWED' in output\
        or 'active' in output:
            return 'not_available'
        elif 'NOT FOUND' in output or 'AVAILABLE' in output\
        or 'is free' in output:
            return 'available'
        elif 'exceeded' in output:
            return 'throttled'
        return 'unknown'
    except subprocess.CalledProcessError:
        return 'error'
    except subprocess.TimeoutExpired:
        return 'timeout'

def main(argv):
    parser = argparse.ArgumentParser(
        description="""Finds domain hacks and tests them to see if
        they are registered."""
    )
    parser.add_argument(
        "min",
        help="Minimum length of domain",
        default=4, type=int
    )
    parser.add_argument(
        "max",
        help="Maximum length of domain",
        default=5, type=int
    )
    parser.add_argument(
        "tld",
        help="Top level domain to use",
        default=".com"
    )
    parser.add_argument(
        "-f",
        help="Dictionary file to use",
        dest="file", default="dictionary.txt"
    )
    parser.add_argument(
        "-d",
        help="Delay",
        dest="delay", default=2.0, type=float
    )

    args = parser.parse_args()
    length_min = args.min
    length_max = args.max
    tld = args.tld
    dict_file = args.file
    chars = "abcdefghijklmnopqrstuvwxyz"
    delay = args.delay

    # Load dictionary, check for lines ending with tld
    domains = []
    with open(dict_file) as f:
        for line in f:
            line = line[0:-1].lower()
            if(line.endswith(tld)) and '-' not in line:
                if len(line) >= length_min and len(line) <= length_max:
                    domain = line[0:-(len(tld))] + "." + tld
                    domains.append(domain)

    print("Checking %s domains..." % len(domains))

    f = open('log.txt', 'a')
    f.write('\n{}\n'.format(datetime.datetime.now()))

    # Try to get whois information for domain to see if it is available or not
    for i in range(len(domains)):
        print("[" + str(i+1) + "/" + str(len(domains)) + "] " + domains[i], end=" -> ", flush=True)
        domain = domains[i]
        status = check_domain(domain)
        if status == 'not_available':
            print("\033[31mnot available\033[0m")
            f.write('{} is not available\n'.format(domains[i]))
        elif status == 'available':
            print("\033[32mavailable\033[0m")
            f.write('{} is available\n'.format(domains[i]))
        elif status == 'throttled':
            print('throttled')
        elif status == 'unknown':
            print("\033[33munknown\033[0m")
            f.write('{} might be available\n'.format(domains[i]))
            print(process.stdout)
        elif status == 'error':
            print('error')
        elif status == 'timeout':
            print('timeout')

        time.sleep(delay)

    f.close()

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('Interrupted by user.')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
