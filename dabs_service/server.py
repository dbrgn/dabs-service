# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import os
import urllib
from datetime import datetime, timedelta

import pytz
from bottle import route, run, request, response, static_file

from .extraction import extract_map, extract_text, ExtractionError


TEMPPATH = os.environ.get('TEMPPATH', os.path.abspath('.'))


class TargetDay(object):
    """A wrapper for the target day."""

    def __init__(self, name):
        assert name in ['today', 'tomorrow']
        self._name = name
        swiss_timezone = pytz.timezone('Europe/Zurich')
        self._dateobj = datetime.now(swiss_timezone).date()
        if name == 'tomorrow':
            self._dateobj += timedelta(days=1)

    @property
    def date(self):
        return self._dateobj

    @property
    def name(self):
        return self._name

    @property
    def datestring(self):
        return self.date.strftime('%Y%m%d')


def get_filepath(day):
    return os.path.join(TEMPPATH, 'DABS_{0}.pdf'.format(day.datestring))


def download_dabs(day):
    """Download the DABS PDF.

    Args:
        target_date:
            Either ``today`` or ``tomorrow``.

    Returns:
        The filepath of the DABS PDF.

    """
    filepath = get_filepath(day)
    url = 'http://www.skyguide.ch/fileadmin/dabs-{day.name}/DABS_{day.datestring}.pdf'
    urllib.urlretrieve(url.format(day=day), filepath)
    return filepath


def process_dabs(day, target, filepath=None):
    """Process the specified DABS file. Return response content.

    Args:
        day:
            A ``TargetDay`` instance.
        target:
            Either ``map`` or ``text``.
        filepath:
            Optional. Filepath to the DABS PDF file. If no ``filepath`` is
            specified, it is calculated using the ``day`` parameter.

    Returns:
        Response content. Content type is also set using the global response
        object.

    """
    # If necessary, obtail filepath
    if filepath is None:
        filepath = get_filepath(day)

    # Handle map extraction
    if target == 'map':
        map_filename = 'map_{0}.png'.format(day.datestring)
        extract_map(filepath, os.path.join(TEMPPATH, map_filename))
        return static_file(map_filename, root=TEMPPATH, mimetype='image/png')

    # Handle text extraction
    elif target == 'text':
        try:
            data = extract_text(filepath)
        except ExtractionError as e:
            response.status = 500
            return unicode(e)
        mime = request.headers.get('Accept').lower()
        print(mime)
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
        elif mime == 'text/tsv':
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
        return 'Invalid target: "{0}"'.format(target)


@route('/')
def index():
    return 'DABS webservice'


@route('/today/<target>/')
def today(target):
    day = TargetDay('today')
    filepath = download_dabs(day)
    return process_dabs(day, target, filepath)


@route('/tomorrow/<target>/')
def tomorrow(target):
    day = TargetDay('tomorrow')
    filepath = download_dabs(day)
    return process_dabs(day, target, filepath)


if __name__ == '__main__':
    if os.environ.get('USE_GUNICORN', '').lower() in ['y', 'yes', '1', 'true']:
        port = int(os.environ.get('PORT', 8000))
        run(server='gunicorn', host='0.0.0.0', port=port)
    else:
        run(host='0.0.0.0', port=8000)
