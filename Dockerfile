FROM grahamdumpleton/mod-wsgi-docker:python-3.5-onbuild
ARG LOCAL_PKG
ARG TRANSPORT_URL
RUN mkdir /setup
ADD * /setup
RUN pip install -r /setup/requirements.txt
RUN ls /setup
# next line we want to remove the upstream package if
# user want to test it locally
# example oslo.messaging where LOCAL_PKG="oslo.messaging"
# (extracted from the basename)
RUN if [ -d /app/$LOCAL_PKG ]; then cd /app/$LOCAL_PKG; pip uninstall -y $LOCAL_PKG; python setup.py develop; fi
CMD ["server-eventlet.wsgi"]
