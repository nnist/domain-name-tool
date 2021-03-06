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
    def setUp(self):
        self.dc = DomainChecker(delay=1.5)

    def test_check_domain(self):
        """Test the check_domain method."""
        assert self.dc.check_domain('ado.be') == 'not_available'
        assert self.dc.check_domain('jhgtyasjkhjdffd.be') == 'available'
    
    def test_check_domains_returns_correct_results(self):
        domains = ['ab.be', 'ado.be', 'foredescri.be']
        results = self.dc.check_domains(domains)
        expected_results = [('ab.be', 'not_available'),
                           ('ado.be', 'not_available'),
                           ('foredescri.be', 'available')]
        assert results == expected_results
    
    def test_get_tld_list_returns_list_of_proper_length(self):
        tld_list = self.dc.get_tld_list()
        # 1541 TLDs in total at 27 aug 2018. This number will only increase,
        # so testing for at least 1500 should be safe.
        assert len(tld_list) > 1500

    def test_get_domains_returns_correct_domains(self):
        dc = DomainChecker(1, 20, delay=1.5)
        tld_list = dc.get_tld_list()
        domains = dc.get_domains('sadnessparty', tld_list)
        assert domains == ['sadness.party']
        domains = dc.get_domains('cathode', tld_list)
        assert domains == ['catho.de']
        domains = dc.get_domains('aerobe', tld_list)
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
            assert process_output[0] == b'usage: domaintool.py [-h] [-v] [--min MIN] [--max MAX] [--tld TLD]'
            assert process_output[1].strip() == b'[-f WORDLIST] [-d DELAY]'

    def test_cli(self):
        """Test the cli."""
        with patch('sys.stdout', new=StringIO()) as output:
            process = subprocess.run(['python3 domaintool/domaintool.py --min 13 --max 13 --tld be -d 0.1'],
                                     shell=True,
                                     timeout=30,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, check=True)
            assert process.returncode == 0
            
            with open('log.txt', 'r') as f:
                lines = f.read().splitlines()
                assert 'INFO: Finding words ending with .be TLD in english.txt.' in lines[0]
                assert 'INFO: Checking 9 domains...' in lines[2]
