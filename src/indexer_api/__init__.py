"""
IndexerAPI - Enterprise File Indexing Service

A production-ready REST API for file system indexing and search.
"""
__version__ = "1.0.0"
__author__ = "IndexerSuite Team"

from indexer_api.main import app, create_app

__all__ = ["app", "create_app", "__version__"]
