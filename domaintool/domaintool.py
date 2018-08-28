"""Get domain hacks from a dictionary and test them for availability."""
# https://en.wikipedia.org/wiki/Domain_hack
import datetime
import argparse
import sys
import os
import time
import subprocess
import logging as log

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
        """Return a list with all possible top level domains."""
        tld_list = []
        with open('top-level-domains.txt', 'r') as f:
            lines = f.read().splitlines()
            for line in lines[1:]:
                tld_list.append(line.lower())

        return tld_list

    def get_domains(self, word, tld_list):
        """Take a word, find fitting TLDs and return them.

        >>> find_tlds('scuba')
        ['scu.ba']

        >>> find_tlds('cathode')
        ['catho.de']
        """
        domains = []
        for tld in tld_list:
            if word.endswith(tld):
                if len(word) >= self.length_min\
                and len(word) <= self.length_max:
                    domain = word[0:-(len(tld))] + "." + tld
                    domains.append(domain)

        return domains

    def check_domains(self, domains):
        """Check a list of domains for availability."""
        log.info("Checking %s domains..." % len(domains))

        # Try to get whois information for domain to see if it is available
        for domain in enumerate(domains):
            status = self.check_domain(domain[1])
            result = ''
            if status == 'not_available':
                result = '\033[31mnot available\033[0m'
            elif status == 'available':
                result = '\033[32mavailable\033[0m'
            elif status == 'throttled':
                result = 'throttled'
            elif status == 'unknown':
                result = '\033[33munknown\033[0m'
            elif status == 'error':
                result = 'error'
            elif status == 'timeout':
                result = 'timeout'

            msg = '[{}/{}] {} -> {}'.format(str(domain[0] + 1),
                                            str(len(domains)), domain[1],
                                            result)
            log.info(msg)
            time.sleep(self.delay)

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

            log.debug(process.stdout)
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
        '-v', '--verbose', help="verbose mode", action='store_true'
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

    log.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                    level=log.DEBUG, datefmt='%d-%m-%y %H:%M:%S',
                    filename='log.txt', filemode='w')
    console = log.StreamHandler()
    
    if args.verbose:
        log.info("Verbose output.")
        console.setLevel(log.DEBUG)
        formatter = log.Formatter('%(asctime)s %(levelname)s: %(message)s',
                                  datefmt='%d-%m-%y %H:%M:%S')
        console.setFormatter(formatter)
    else:
        console.setLevel(log.INFO)
        formatter = log.Formatter('%(message)s')
        console.setFormatter(formatter)

    log.getLogger('').addHandler(console)

    domain_checker = DomainChecker(args.min, args.max, args.file,
                                   chars, args.delay)
    domains = []
    
    tld_list = domain_checker.get_tld_list()
    if args.tld != 'any':
        if args.tld in tld_list:
            tld_list = [args.tld]
        else:
            log.error('error: invalid TLD')
            exit(1)
    
    if args.tld == 'any':
        log.info('Finding words ending with any TLD in {}.'.format(args.file))
    else:
        log.info('Finding words ending with .{} TLD in {}.'.format(args.tld, args.file))
    
    with open(args.file, 'r') as f:
        lines = f.read().splitlines()
        for line in enumerate(lines):
            domains_ = domain_checker.get_domains(line[1], tld_list)
            update_progress_bar(line[0], len(lines))
            if domains_:
                for domain in domains_:
                    domains.append(domain)
    
    update_progress_bar(len(lines), len(lines))
    log.info('Found {} possible domains.'.format(len(domains)))
    domain_checker.check_domains(domains)
    log.shutdown()

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        log.info('Interrupted by user.')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0) # pylint: disable=protected-access
