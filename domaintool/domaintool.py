"""Get domain hacks from a dictionary and test them for availability."""
# https://en.wikipedia.org/wiki/Domain_hack
import datetime
import argparse
import sys
import os
import time
import subprocess

def update_progress_bar(current, total):
    bar_length = 10
    progress = current / total
    blocks = int(round(bar_length * progress))
    text = '\rProgress: {} {}/{} {:.1f}%'\
            .format('▇' * blocks + '-' * (bar_length - blocks),
                    current, total, progress * 100)
    if progress == 1:
        text += '\n'

    sys.stdout.write(text)
    sys.stdout.flush()

class DomainChecker():
    """Get domain hacks from a dictionary and test them for availability."""
    def __init__(self, length_min, length_max, dict_file="dictionary.txt",
                 chars="abcdefghijklmnopqrstuvwxyz", delay=2.0):
        self.length_min = length_min
        self.length_max = length_max
        self.dict_file = dict_file
        self.chars = chars
        self.delay = delay

    def get_tld_list(self):
        tld_list = []
        with open('top-level-domains.txt', 'r') as f:
            lines = f.read().splitlines()
            for line in lines[1:]:
                tld_list.append(line.lower())

        return tld_list

    def find_tlds(self, word):
        """Take a word, find fitting TLDs and return them."""
        tlds = []
        tld_list = self.get_tld_list()
        for tld in tld_list:
            if word.endswith(tld):
                tlds.append(tld)

        return tlds

    def get_domains(self, tld):
        """Load dictionary and return lines ending with tld"""
        domains = []
        with open(self.dict_file) as f:
            for line in f:
                line = line[0:-1].lower()
                if(line.endswith(tld)) and '-' not in line:
                    if len(line) >= self.length_min\
                    and len(line) <= self.length_max:
                        domain = line[0:-(len(tld))] + "." + tld
                        domains.append(domain)
        return domains

    def check_domains(self, domains):
        """Check a list of domains for availability."""
        print("Checking %s domains..." % len(domains))

        f = open('log.txt', 'a')
        f.write('\n{}\n'.format(datetime.datetime.now()))

        # Try to get whois information for domain to see if it is available
        for domain in enumerate(domains):
            print("[" + str(domain[0] + 1) + "/" + str(len(domains)) + "] " +
                  domain[1], end=" -> ", flush=True)
            status = self.check_domain(domain[1])
            if status == 'not_available':
                print("\033[31mnot available\033[0m")
                f.write('{} is not available\n'.format(domain[1]))
            elif status == 'available':
                print("\033[32mavailable\033[0m")
                f.write('{} is available\n'.format(domain[1]))
            elif status == 'throttled':
                print('throttled')
            elif status == 'unknown':
                print("\033[33munknown\033[0m")
                f.write('{} might be available\n'.format(domain[1]))
            elif status == 'error':
                print('error')
            elif status == 'timeout':
                print('timeout')

            time.sleep(self.delay)

        f.close()

    def check_domain(self, domain):
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

            print(process.stdout)
            return 'unknown'
        except subprocess.CalledProcessError:
            return 'error'
        except subprocess.TimeoutExpired:
            return 'timeout'

def main(argv):
    """Get domain hacks from a dictionary and test them for availability."""
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
        "--tld",
        help="Top level domain to use. 'any' by default.",
        default='any'
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

    args = parser.parse_args(argv)
    chars = "abcdefghijklmnopqrstuvwxyz"

    domain_checker = DomainChecker(args.min, args.max, args.file,
                                   chars, args.delay)
    domains = []
    
    if args.tld == 'any':
        print('Finding words ending with any TLD in {}.'.format(args.file))
        tld_list = domain_checker.get_tld_list()
        for tld in enumerate(tld_list):
            domains_ = domain_checker.get_domains(tld[1])
            update_progress_bar(tld[0], len(tld_list))
            if domains_:
                for domain in domains_:
                    domains.append(domain)

        update_progress_bar(len(tld_list), len(tld_list))
        print('Found {} possible domains.'.format(len(domains)))
    else:
        domains = domain_checker.get_domains(args.tld)

    domain_checker.check_domains(domains)

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('Interrupted by user.')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0) # pylint: disable=protected-access
