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
def map_filepath():
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=True)
    return tmp.name


def test_map_extraction(map_filepath):
    dabs_filepath = os.path.join(TEST_DIR, 'DABS_20130726.pdf')
    try:
        retval = extraction.extract_map(dabs_filepath, map_filepath)
    except subprocess.CalledProcessError:
        pytest.fail()
    filetype = subprocess.check_output(['file', map_filepath])
    assert 'PNG image data' in filetype


def test_text_extraction_20130726():
    dabs_filepath = os.path.join(TEST_DIR, 'DABS_20130726.pdf')
    data = extraction.extract_text(dabs_filepath)
    lines = data.csv.split('\r\n')
    assert lines[0] == b'"Firing-Nr\nD-/R-Area\nNOTAM-Nr",Validity UTC,"Lower Limit\nAMSL or FL","Upper Limit\nAMSL or FL",Location,Center Point,Covering Radius,Activity / Remarks'
    assert lines[1] == b'D-12,"0600 - 1000\n1100 - 1600",GND,1800m / 5950ft,SIHLTAL,470140N 0085126E,3.6 KM/1.9 NM,D-AREA ACTIVE'
    assert lines[2] == b'W0631/13,0800 - 0900,GND,FL100,WANGEN LACHEN AD,471219N 0085202E,10.0 KM/5.4 NM,"R-AREA ACT. ENTRY PROHIBITED.\nFOR INFO CTC ZURICH INFO 124.7"'
    assert lines[3] == b'W0887/13,1145 - 1245,GND,FL100,4.7 KM NW MEIRINGEN,464530N 0080830E,7.0 KM/3.8 NM,"R-AREA ACT. ENTRY PROHIBITED.\nFOR INFO CTC ZURICH INFO 124.7"'
    assert lines[4] == b'W0895/13,0745 - 0845,GND,FL080,ZUG,471017N 0083113E,7.1 KM/3.8 NM,"R-AREA ACT. ENTRY PROHIBITED.\nFOR INFO CTC ZURICH INFO 124.7"'
    assert lines[5] == b'W0791/13,0800 - 1910,GND,FL100,SAANEN,462923N 0071542E,9.3 KM/5.0 NM,"INTENSE GLIDER ACTIVITY\nIN VICINITY OF SAANEN"'
    assert lines[6] == b'W0837/13,0600 - 2000,GND,FL100,ZWEISIMMEN,463311N 0072250E,9.3 KM/5.0 NM,"INTENSE GLIDER ACTIVITY\nIN VICINITY OF ZWEISIMMEN"'


def test_text_extraction_20131106():
    dabs_filepath = os.path.join(TEST_DIR, 'DABS_20131106.pdf')
    data = extraction.extract_text(dabs_filepath)
    lines = data.csv.split('\r\n')
    assert lines[0] == b'"Firing-Nr\nD-/R-Area\nNOTAM-Nr",Validity UTC,"Lower Limit\nAMSL or FL","Upper Limit\nAMSL or FL",Location,Center Point,Covering Radius,Activity / Remarks'
    assert lines[1] == b'4501,0800 - 1700,GND,6600m / 21700ft,1.5 KM WSW SIMPLON,461133N 0080215E,8.4 KM/4.5 NM,FIRING'
    assert lines[2] == b'4502,0730 - 1500,GND,2700m / 8900ft,4.4 KM ENE FLUEHLI,465410N 0080401E,4.0 KM/2.2 NM,FLARE AND CHAFF FIRING'
    assert lines[3] == b'D-12,"0700 - 1100\n1200 - 2100",GND,3000m / 9850ft,SIHLTAL,470140N 0085126E,3.6 KM/1.9 NM,D-AREA ACTIVE'
    assert lines[4] == b'R-3,"1240 - 1320\n1440 - 1520",FL100,FL130,SPEER,471047N 0091932E,24.3 KM/13.1 NM,R-AREA ACTIVE'
    assert lines[5] == b'R-4,"0800 - 1100\n1230 - 1500",GND,2700m / 8900ft,LAC DE NEUCHATEL,465322N 0065000E,9.9 KM/5.4 NM,R-AREA ACTIVE'
    assert lines[6] == b'R-4A,"0800 - 1100\n1230 - 1500",1500m / 5000ft,2700m / 8900ft,LAC DE NEUCHATEL,465520N 0064423E,13.7 KM/7.4 NM,R-AREA ACTIVE'
    assert lines[7] == b'R-6,"0745 - 1100\n1230 - 1530",1800m / 6000ft,FL130,AXALP,464400N 0080322E,13.2 KM/7.1 NM,R-AREA ACTIVE'
    assert lines[8] == b'R-11,"0730 - 1030\n1230 - 1530",GND,9600m / 31500ft,S-CHANF,464056N 0095708E,8.9 KM/4.8 NM,R-AREA ACTIVE'
    assert lines[9] == b'R-11A,"0730 - 1030\n1230 - 1530",2100m / 7000ft,9600m / 31500ft,S-CHANF,463605N 0095959E,8.2 KM/4.5 NM,R-AREA ACTIVE'
    assert lines[10] == b'B1313/13,"0630 - 1105\n1215 - 1605",REF AIP,REF AIP,SION TEMPO MIL TMA ALL SECT,461816N 0073734E,15.0 KM/8.1 NM,MIL TMA ACTIVE'
    assert lines[11] == b'B1314/13,"0630 - 1105\n1215 - 1605",REF AIP,REF AIP,LOCARNO TEMPO MIL TMA ALL SECT,461420N 0085140E,30.0 KM/16.2 NM,MIL TMA ACTIVE'
    assert lines[12] == b'B1394/13,"0630 - 1105\n1215 - 2100",700m / 2300ft,FL130,ALPNACH TEMPO MIL TMA SECT 2,465150N 0081222E,6.1 KM/3.3 NM,TMA ACTIVE'
