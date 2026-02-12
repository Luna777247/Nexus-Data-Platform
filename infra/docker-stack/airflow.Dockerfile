FROM apache/airflow:2.7.0-python3.11

USER root
RUN apt-get update \
	&& apt-get install -y --no-install-recommends openjdk-17-jre-headless \
	&& rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

COPY requirements-airflow.txt /requirements-airflow.txt
USER airflow
RUN pip install --no-cache-dir -r /requirements-airflow.txt
