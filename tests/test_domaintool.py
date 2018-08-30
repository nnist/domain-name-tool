"""Test the domain name tool."""
import unittest
from unittest.mock import patch
from io import StringIO
import subprocess
import logging as log
import sys
from domaintool.domaintool import DomainChecker

logger = log.getLogger()
logger.level = log.DEBUG

class DomaintoolTest(unittest.TestCase):
    def test_check_domain(self):
        """Test the check_domain method."""
        domain_checker = DomainChecker(3, 4, delay=1.5)
        assert domain_checker.check_domain('ado.be') == 'not_available'
        assert domain_checker.check_domain('jhgtyasjkhjdffd.be') == 'available'
    
    def test_check_domains(self):
        """Test the check_domains method."""
        pass
        #with patch('sys.stdout', new=StringIO()) as output:
        #    domain_checker = DomainChecker(13, 13, delay=0.1)
        #    domains = domain_checker.get_domains(['be'])
        #    domain_checker.check_domains(domains)
        #    output = output.getvalue().split('\n')
        #    assert output[0] == 'Checking 7 domains...'
    
    def test_get_tld_list_returns_list_of_proper_length(self):
        domain_checker = DomainChecker(3, 4, delay=1.5)
        tld_list = domain_checker.get_tld_list()
        # 1541 TLDs in total at 27 aug 2018. This number will only increase,
        # so testing for at least 1500 should be safe.
        assert len(tld_list) > 1500

    def test_get_domains_returns_correct_domains(self):
        domain_checker = DomainChecker(1, 20, delay=1.5)
        tld_list = domain_checker.get_tld_list()
        domains = domain_checker.get_domains('sadnessparty', tld_list)
        assert domains == ['sadness.party']
        domains = domain_checker.get_domains('cathode', tld_list)
        assert domains == ['catho.de']
        domains = domain_checker.get_domains('aerobe', tld_list)
        assert domains == ['aero.be']

    def test_cli_help_prints_correct_output(self):
        with patch('sys.stdout', new=StringIO()) as output:
            process = subprocess.run(['python3 domaintool/domaintool.py -h'],
                                     shell=True,
                                     timeout=10,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, check=True)
            assert process.returncode == 0
            process_output = process.stdout.split(b'\n')
            assert process_output[0] == b'usage: domaintool.py [-h] [-v] [--tld TLD] [-f FILE] [-d DELAY] min max'

    def test_cli(self):
        """Test the cli."""
        with patch('sys.stdout', new=StringIO()) as output:
            process = subprocess.run(['python3 domaintool/domaintool.py 13 13 --tld be -d 0.1'],
                                     shell=True,
                                     timeout=10,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, check=True)
            assert process.returncode == 0
            
            with open('log.txt', 'r') as f:
                lines = f.read().splitlines()
                assert 'INFO: Finding words ending with .be TLD in english.txt.' in lines[0]
                assert 'INFO: Checking 9 domains...' in lines[2]
