# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import os
import logging
from datetime import datetime, timedelta

import pytz
import requests
import bottle
from bottle import run, request, response, static_file

from .extraction import extract_map, compress_map, extract_text, ExtractionError
from .lib.bottle_redis import RedisPlugin


logging.basicConfig(level=logging.INFO)

TEMPPATH = os.environ.get('TEMPPATH', os.path.abspath('.'))

app = bottle.Bottle()
plugin = RedisPlugin(os.environ.get('REDIS_URL', 'redis://localhost/3'))
app.install(plugin)


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

    @property
    def prev_datestring(self):
        """Return the datestring for the day before the current date."""
        return (self.date - timedelta(1)).strftime('%Y%m%d')


def get_filepath(day):
    return os.path.join(TEMPPATH, 'DABS_{0}.pdf'.format(day.datestring))


def download_dabs(day, rdb):
    """Download the DABS PDF.

    Args:
        target_date:
            Either ``today`` or ``tomorrow``.

    Returns:
        (filepath, has_changed)

        - The filepath of the DABS PDF.
        - Whether the PDF has changed or not.

    """
    # Prepare filepath and URL
    filepath = get_filepath(day)
    url = 'http://www.skyguide.ch/fileadmin/dabs-{d.name}/DABS_{d.datestring}.pdf'.format(d=day)

    # Handle caching
    headers = {}
    if rdb.exists('etag_' + url) and os.path.isfile(filepath):
        headers['If-None-Match'] = rdb.get('etag_' + url)

    # Request file
    r = requests.get(url, headers=headers, stream=True)

    # Download file if necessary
    if r.status_code == requests.codes.not_modified:
        logging.info("ETag didn't change, using cached file.")
        return filepath, False
    elif r.status_code == 200:
        logging.info('Re-downloading file DABS_{d.datestring}.pdf'.format(d=day))
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        rdb.set('etag_' + url, r.headers['etag'])
        return filepath, True
    else:
        msg = 'Something went wrong (HTTP {0.status_code})'.format(r)
        logging.error(msg)
        raise RuntimeError(msg)

    # TODO: If download isn't a PDF file, retry with previous date
    #if http_msg.subtype != 'pdf':
    #    log_msg = 'Downloaded filetype is {0} instead of pdf, trying previous day...'
    #    logging.info(log_msg.format(http_msg.subtype))

    #    url = 'http://www.skyguide.ch/fileadmin/dabs-{day.name}/DABS_{day.prev_datestring}.pdf'
    #    _, http_msg = urllib.urlretrieve(url.format(day=day), filepath)

    #    # If it fails again, raise an exception
    #    if http_msg.subtype != 'pdf':
    #        raise RuntimeError('Could not find valid PDF download.')


def process_dabs(day, target, rdb, filepath=None, has_changed=True):
    """Process the specified DABS file. Return response content.

    Args:
        day:
            A ``TargetDay`` instance.
        target:
            Either ``map`` or ``text``.
        rdb:
            A ``redis.StrictRedis`` instance.
        filepath:
            Optional. Filepath to the DABS PDF file. If no ``filepath`` is
            specified, it is calculated using the ``day`` parameter.
        has_changed:
            Optional. Whether the DABS PDF has changed or not. Default ``True``.

    Returns:
        Response content. Content type is also set using the global response
        object.

    """
    # If necessary, obtail filepath
    if filepath is None:
        filepath = get_filepath(day)

    # Handle map extraction
    if target == 'map':
        pngfile = 'map_{0}.png'.format(day.datestring)
        jpgfile = 'map_{0}.jpg'.format(day.datestring)
        pngpath = os.path.join(TEMPPATH, pngfile)
        jpgpath = os.path.join(TEMPPATH, jpgfile)
        if has_changed or not os.path.isfile(jpgpath):
            logging.info('Extracting map from PDF...')
            extract_map(filepath, pngpath)
            logging.info('Compressing image...')
            compress_map(pngpath, jpgpath)
        else:
            logging.info('Using cached map image.')
        return static_file(jpgfile, root=TEMPPATH, mimetype='image/jpeg')

    # Handle text extraction
    # TODO caching
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


@app.route('/')
def index():
    return 'DABS webservice.'


@app.route('/today/<target>/')
def today(target, rdb):
    """
    :param rdb: Redis instance.
    :type rdb: redis.StrictRedis
    """
    day = TargetDay('today')
    try:
        filepath, has_changed = download_dabs(day, rdb)
    except RuntimeError as e:
        response.status = 500
        return unicode(e)
    return process_dabs(day, target, rdb, filepath, has_changed)


@app.route('/tomorrow/<target>/')
def tomorrow(target, rdb):
    """
    :param rdb: Redis instance.
    :type rdb: redis.StrictRedis
    """
    day = TargetDay('tomorrow')
    try:
        filepath, has_changed = download_dabs(day, rdb)
    except RuntimeError as e:
        response.status = 500
        return unicode(e)
    return process_dabs(day, target, rdb, filepath, has_changed)


if __name__ == '__main__':
    if os.environ.get('USE_GUNICORN', '').lower() in ['y', 'yes', '1', 'true']:
        port = int(os.environ.get('PORT', 8000))
        run(app, server='gunicorn', host='0.0.0.0', port=port)
    else:
        run(app, host='0.0.0.0', port=8000)
