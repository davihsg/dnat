FROM registry.scontain.com/sconecuratedimages/apps:python-3.10.5-alpine-scone5.8.0

WORKDIR /app
RUN pip install --no-cache-dir cryptography
COPY executor.py /app/

ENV SCONE_MODE=HW
ENV SCONE_LOG=3
ENV ENCRYPTED_CODE=/data/hello.py.enc

CMD ["python", "/app/executor.py"]

