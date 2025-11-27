FROM registry.scontain.com/sconecuratedimages/apps:python3.10.5-alpine3.15-scone5.8-pre-release

WORKDIR /app

# Install dependencies for ML/data processing
RUN pip install --no-cache-dir \
    pycryptodome \
    pandas \
    numpy \
    scikit-learn

# Copy execution script
COPY execute.py /app/

# SCONE configuration
ENV SCONE_MODE=HW
ENV SCONE_LOG=3
ENV SCONE_ALLOW_DLOPEN=2

CMD ["python", "/app/execute.py"]

