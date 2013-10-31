dabs-service
============

This is a small webservice that downloads today's and tomorrow's DABS (Daily
Airspace Bulletin Switzerland) from Skyguide and tries to parse it.

You can find the DABS here: http://www.skyguide.ch/en/nc/services/aim-services/dabs/

There are two parts that can be returned: The map (page 1) and the tabular data
(page 2).

The service is powered by `bottle <http://bottlepy.org/>`__ and `tablib
<http://python-tablib.org/>`__.


Usage
-----

To fetch data from the API, simply send a ``GET`` request with the appropriate
``Accept`` header to the endpoints.

Endpoints
~~~~~~~~~ 

- ``/today/map/``
- ``/today/text/``
- ``/tomorrow/map/``
- ``/tomorrow/text/``

Content-Types
~~~~~~~~~~~~~

Valid for text response only. Can be set using the ``Accept`` HTTP header.

- csv: ``text/csv``
- tsv: ``text/tsv``
- json: ``application/json``
- yaml: ``text/yaml`` / ``text/x-yaml`` / ``application/yaml`` / ``application/x-yaml``
- html: ``text/html``
- ods: ``application/vnd.oasis.opendocument.spreadsheet``
- xls: ``application/vnd.ms-excel``
- xlsx: ``application/vnd.openxmlformats-officedocument.spreadsheetml.sheet``

Fallback/default is HTML format.

The ``.../map/`` will always return a JPG image.

Example
~~~~~~~

::

    $ curl -H "Accept: text/csv" http://localhost:8000/today/text/
    "Firing-Nr
    D-/R-Area
    NOTAM-Nr",Validity UTC,"Lower Limit
    AMSL or FL","Upper Limit
    AMSL or FL",Location,Center Point,Covering Radius,Activity / Remarks
    D-12,"0600 - 1000
    1100 - 1600",GND,1800m / 5950ft,SIHLTAL,470140N 0085126E,3.6 KM/1.9 NM,D-AREA ACTIVE
    W0631/13,0800 - 0900,GND,FL100,WANGEN LACHEN AD,471219N 0085202E,10.0 KM/5.4 NM,"R-AREA ACT. ENTRY PROHIBITED.
    FOR INFO CTC ZURICH INFO 124.7"
    W0887/13,1145 - 1245,GND,FL100,4.7 KM NW MEIRINGEN,464530N 0080830E,7.0 KM/3.8 NM,"R-AREA ACT. ENTRY PROHIBITED.
    FOR INFO CTC ZURICH INFO 124.7"
    W0895/13,0745 - 0845,GND,FL080,ZUG,471017N 0083113E,7.1 KM/3.8 NM,"R-AREA ACT. ENTRY PROHIBITED.
    FOR INFO CTC ZURICH INFO 124.7"
    W0791/13,0800 - 1910,GND,FL100,SAANEN,462923N 0071542E,9.3 KM/5.0 NM,"INTENSE GLIDER ACTIVITY
    IN VICINITY OF SAANEN"
    W0837/13,0600 - 2000,GND,FL100,ZWEISIMMEN,463311N 0072250E,9.3 KM/5.0 NM,"INTENSE GLIDER ACTIVITY
    IN VICINITY OF ZWEISIMMEN"


Running the Server
------------------

To start the development server, simply run the following command::

    $ python -m dabs_service.server

In production it is recommended to use a more robust WSGI server than the
builtin bottle development server.


Testing
-------

To run the tests, install ``pytest``, ``pytest-pep8`` and ``pytest-cov``. Then
simply issue the following command in the repo root::

    $ py.test


Author
------

Hi, I'm Danilo Bargen. As a paragliding pilot, I find this kind of information
useful and important, but the PDF version of the DABS by Skyguide is not too
convenient on the go. The service attempts to provide better data for developers
of mobile apps.

- Twitter: http://twitter.com/dbrgn
- Homepage: http://dbrgn.ch/


License
-------

`MIT License <http://www.tldrlegal.com/license/mit-license>`_, see LICENSE file.
