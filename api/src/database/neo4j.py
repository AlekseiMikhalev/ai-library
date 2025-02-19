"""Database initializer."""

from neo4j import AsyncDriver, AsyncGraphDatabase, Driver, GraphDatabase
from src.config.settings import app_settings


# Dependency to provide the Neo4j async session
def get_neo4j_async() -> AsyncDriver:
    """Get the Neo4j async driver instance."""
    return AsyncGraphDatabase.driver(
        app_settings.NEO4J_URI,
        auth=(app_settings.NEO4J_USER, app_settings.NEO4J_PASSWORD),
        database=app_settings.NEO4J_DB,
    )


# Dependency to provide the Neo4j sync session
def get_neo4j_sync() -> Driver:
    """Get the Neo4j sync driver instance."""
    return GraphDatabase.driver(
        app_settings.NEO4J_URI,
        auth=(app_settings.NEO4J_USER, app_settings.NEO4J_PASSWORD),
        database=app_settings.NEO4J_DB,
    )
