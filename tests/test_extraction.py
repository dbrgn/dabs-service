# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import os.path
import sys
import tempfile
import subprocess

import pytest

sys.path.insert(0, os.path.abspath('..'))
from dabs_service import extraction


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def dabs_filepath():
    filename = 'DABS_20130726.pdf'
    return os.path.join(TEST_DIR, filename)


@pytest.fixture
def map_filepath():
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=True)
    return tmp.name


def test_map_extraction(dabs_filepath, map_filepath):
    try:
        retval = extraction.extract_map(dabs_filepath, map_filepath)
    except subprocess.CalledProcessError:
        pytest.fail()
    filetype = subprocess.check_output(['file', map_filepath])
    assert 'PNG image data' in filetype


def test_text_extraction(dabs_filepath):
    data = extraction.extract_text(dabs_filepath)
    lines = data.csv.split('\r\n')
    assert lines[0] == b'"Firing-Nr\nD-/R-Area\nNOTAM-Nr",Validity UTC,"Lower Limit\nAMSL or FL","Upper Limit\nAMSL or FL",Location,Center Point,Covering Radius,Activity / Remarks'
    assert lines[1] == b'D-12,"0600 - 1000\n1100 - 1600",GND,1800m / 5950ft,SIHLTAL,470140N 0085126E,3.6 KM/1.9 NM,D-AREA ACTIVE'
    assert lines[2] == b'W0631/13,0800 - 0900,GND,FL100,WANGEN LACHEN AD,471219N 0085202E,10.0 KM/5.4 NM,"R-AREA ACT. ENTRY PROHIBITED.\nFOR INFO CTC ZURICH INFO 124.7"'
    assert lines[3] == b'W0887/13,1145 - 1245,GND,FL100,4.7 KM NW MEIRINGEN,464530N 0080830E,7.0 KM/3.8 NM,"R-AREA ACT. ENTRY PROHIBITED.\nFOR INFO CTC ZURICH INFO 124.7"'
    assert lines[4] == b'W0895/13,0745 - 0845,GND,FL080,ZUG,471017N 0083113E,7.1 KM/3.8 NM,"R-AREA ACT. ENTRY PROHIBITED.\nFOR INFO CTC ZURICH INFO 124.7"'
    assert lines[5] == b'W0791/13,0800 - 1910,GND,FL100,SAANEN,462923N 0071542E,9.3 KM/5.0 NM,"INTENSE GLIDER ACTIVITY\nIN VICINITY OF SAANEN"'
    assert lines[6] == b'W0837/13,0600 - 2000,GND,FL100,ZWEISIMMEN,463311N 0072250E,9.3 KM/5.0 NM,"INTENSE GLIDER ACTIVITY\nIN VICINITY OF ZWEISIMMEN"'
