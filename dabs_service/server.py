# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import re
import urllib
import subprocess
from datetime import date

import tablib
from bottle import route, run, request, response, static_file


TEMPPATH = '.'


def extract_map(infile, outfile):
    subprocess.check_call(['mudraw', '-r', '150', '-o', outfile, infile, '1'])
    return outfile


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
        response.status = 500
        return 'Could not extract text from PDF.'
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


@route('/')
def index():
    return 'DABS webservice'


@route('/today/<contenttype>/')
def today(contenttype):
    # Fetch today's DABS from Skyguide
    datestring = date.today().strftime('%Y%m%d')
    filename = 'DABS_{0}.pdf'.format(datestring)
    url = 'http://www.skyguide.ch/fileadmin/dabs-today/' + filename
    urllib.urlretrieve(url.format(datestring), filename)

    # Render image of first page
    if contenttype == 'map':
        map_filename = extract_map(filename, 'map_{0}.png'.format(datestring))
        return static_file(map_filename, root=TEMPPATH, mimetype='image/png')
    elif contenttype == 'text':
        data = extract_text(filename)
        mime = request.headers.get('Accept').lower()
        # JSON
        if mime == 'application/json':
            response.content_type = 'application/json; charset=utf-8'
            return data.json
        # YAML
        elif mime in ['text/yaml', 'text/x-yaml', 'application/yaml', 'application/x-yaml']:
            response.content_type = 'text/x-yaml; charset=utf-8'
            return data.yaml
        # CSV
        elif mime == 'text/csv':
            response.content_type = 'text/csv; charset=utf-8'
            return data.csv
        # TSV
        elif mime == 'application/tsv':
            response.content_type = 'text/tsv; charset=utf-8'
            return data.tsv
        # ODS
        elif mime == 'application/vnd.oasis.opendocument.spreadsheet':
            response.content_type = 'application/vnd.oasis.opendocument.spreadsheet; ' + \
                                    'charset=utf-8'
            return data.ods
        # XLS
        elif mime == 'application/vnd.ms-excel':
            response.content_type = 'application/vnd.ms-excel; charset=utf-8'
            return data.xls
        # XLSX
        elif mime == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            response.content_type = 'application/vnd.openxmlformats-officedocument.' + \
                                    'spreadsheetml.sheet; charset=utf-8'
            return data.xlsx
        # HTML (fallback)
        else:
            response.content_type = 'text/html; charset=utf-8'
            return data.html

    else:
        response.status = 400
        return 'Invalid content type: "{0}"'.format(contenttype)


if __name__ == '__main__':
    run(host='0.0.0.0', port=8000)
