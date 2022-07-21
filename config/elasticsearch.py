"""Elasticsearch configuration file."""
import os


ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
