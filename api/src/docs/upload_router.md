# Upload PDF File

Upload a PDF file to the server for processing.

## Request Body

* `file`: The PDF file to be uploaded.

## Response

* `200`: The file has been successfully uploaded. The response body will contain the document ID.
* `422`: The file is not a valid PDF.

### Example Response

```json
{
    "documentId": "example_document_id"
}
```

### Error Response

```json
{
    "detail": "Invalid PDF file"
}
```
