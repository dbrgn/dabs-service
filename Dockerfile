FROM python:2.7
MAINTAINER Danilo Bargen <mail@dbrgn.ch>

# Env vars
ENV PYTHONUNBUFFERED=1

# Install mupdf
RUN cd /tmp \
    && wget http://mupdf.com/downloads/mupdf-1.7a-source.tar.gz \
    && tar xfvz mupdf-1.7a-source.tar.gz \
    && cd mupdf-1.7a-source \
    && make release \
    && make install \
    && rm /tmp/mupdf-1.7a-source.tar.gz \
    && rm -r /tmp/mupdf-1.7a-source

# Pip dependencies
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Add user
RUN adduser --disabled-password --gecos "" dabs

# Add code
RUN mkdir /code
COPY code /code

# Fix permissions
RUN chown -R dabs:dabs /code

# Entry point
WORKDIR /code
USER dabs
CMD ["python", "-m", "dabs_service.server"]
