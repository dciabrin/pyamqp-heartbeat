FROM grahamdumpleton/mod-wsgi-docker:python-3.5-onbuild
ARG LOCAL_PKG
ARG TRANSPORT_URL
RUN mkdir /setup
ADD ./* /setup
RUN pip install -r /setup/requirements.txt
RUN ls /setup
RUN if [ -d /setup/$LOCAL_PKG ]; then cd /setup/$LOCAL_PKG; python setup.py develop; fi
CMD ["server.wsgi"]
