# API Overview
================

## Introduction
---------------

This module provides a RESTful API for interacting with the AI Library.

## Endpoints
------------

### GET /docs

Returns the API documentation in Markdown format.

### GET /redoc

Returns the API documentation in Redoc format.

### GET /openapi.json

Returns the API documentation in OpenAPI JSON format.

### POST /embeddings

Generates embeddings for a list of sections.

* Request Body: `sections` (list of `SectionData` objects)
* Response: `sections` (list of `SectionData` objects with embeddings)

### POST /clustering

Performs clustering on a list of sections with embeddings.

* Request Body: `sections` (list of `SectionData` objects with embeddings)
* Response: `clusters` (list of `Cluster` objects)

## Models
---------

### SectionData

* `section_name`: string
* `section_text`: string
* `section_paragraphs_data`: list of `ParagraphData` objects
* `embedding`: list of floats (optional)

### Cluster

* `cluster_name`: string
* `sections`: list of `SectionData` objects

## Errors
---------

* `400 Bad Request`: invalid request body or parameters
* `500 Internal Server Error`: unexpected error occurred during processing