# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import re
import subprocess

import tablib


class ExtractionError(RuntimeError):
    pass


def extract_map(infile, outfile):
    """Extract map from first page as PNG.

    Args:
        infile:
            Path to DABS PDF file.
        outfile:
            Path where to save the map PNG.

    Returns:
        True

    Raises:
        subprocess.CalledProcessError:
            Raised if extracting image from PDF file using mudraw fails.

    """
    subprocess.check_call(['mudraw', '-r', '150', '-o', outfile, infile, '1'])
    return True


def extract_text(infile):
    """Extract text from specified PDF and return it as a tablib dataset.

    Args:
        infile:
            The path to a PDF file (string or unicode).

    Returns:
        A ``tablib.Dataset`` object.

    Raises:
        subprocess.CalledProcessError:
            Raised if fetching text from PDF file using mudraw fails.

    """
    # Get text from mudraw
    text = subprocess.check_output(['mudraw', '-t', infile])

    # Cleanup raw text
    match = re.search(
            r'.*?Activity \/ Remarks(?P<table1>.*?)Activities not shown on the ' +
            r'DABS Chart Side:.*?Activity \/ Remarks(?P<table2>.*?)For detailed ' +
            r'information regarding the DABS',
            text,
            re.MULTILINE | re.DOTALL)
    if not match:
        raise ExtractionError('Could not extract text from PDF.')
    data = '\n\n\n'.join(match.groups())
    raw_parts = re.sub(r'\n[ \t]+\n', '\n\n', data).split('\n\n\n')
    parts = filter(None, map(lambda x: x.strip(), raw_parts))

    # Write CSV
    headers = (
        b'Firing-Nr\nD-/R-Area\nNOTAM-Nr',
        b'Validity UTC',
        b'Lower Limit\nAMSL or FL',
        b'Upper Limit\nAMSL or FL',
        b'Location',
        b'Center Point',
        b'Covering Radius',
        b'Activity / Remarks',
    )
    rows = []
    for part in parts:
        # Regexes
        multiple_newlines_re = re.compile(r'\n+')
        height_re = re.compile(r'(GND|[0-9]+m \/ [0-9]+ft|FL[0-9]{2,3})')
        center_radius_re = re.compile(r'([0-9]{6}N [0-9]{7}E)\s+?(.*?NM)')

        # Separate columns (warning: hackish code ahead!)
        row = {}
        step1 = re.split(r'([0-2][0-9][0-6][0-9] - [0-2][0-9][0-6][0-9])', part)
        row['nr'] = step1[0].strip()
        timestring = '\n'.join(step1[1:-1])
        row['validity'] = multiple_newlines_re.sub('\n', timestring)
        step2 = filter(None, height_re.split(step1[-1].strip()))
        row['lower'] = step2[0]
        row['upper'] = step2[2]
        step3 = filter(None, center_radius_re.split(step2[-1].strip()))
        row['location'] = step3[0].strip()
        row['center'] = step3[1].strip()
        row['radius'] = step3[2].strip()
        row['activity'] = multiple_newlines_re.sub('\n', step3[3].strip())

        # Add to list of rows
        rows.append((
            row['nr'].encode('utf8'),
            row['validity'].encode('utf8'),
            row['lower'].encode('utf8'),
            row['upper'].encode('utf8'),
            row['location'].encode('utf8'),
            row['center'].encode('utf8'),
            row['radius'].encode('utf8'),
            row['activity'].encode('utf8'),
        ))

    return tablib.Dataset(*rows, headers=headers)
