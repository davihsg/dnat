FROM registry.scontain.com/sconecuratedimages/apps:python-3.7.3-alpine3.10-scone6.0.2

WORKDIR /app
RUN pip install --no-cache-dir cryptography
COPY executor.py /app/

ENV SCONE_MODE=HW
ENV SCONE_LOG=3
ENV ENCRYPTED_CODE=/data/hello.py.enc

CMD ["python", "/app/executor.py"]

