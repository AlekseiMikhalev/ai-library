## Retrieval Router

This router provides endpoints for retrieving relevant knowledge from the AI Library.

### POST /search-concept

Search for concepts in the AI Library based on a user query.

#### Request Body

* `query`: string - User query to search for concepts.

#### Response

* `results`: list of `Result` objects - Search results.

#### Example Request

```http
POST /search-concept HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "query": "Neural Networks"
}
```

#### Example Response

```json
{
    "results": [
        {
            "id": "1",
            "title": "Introduction to Neural Networks",
            "book": "Deep Learning Fundamentals",
            "author": "Andrew Johnson",
            "page": 42,
            "relevance": 0.95,
            "excerpt": "Neural networks are computational models inspired by the human brain's structure and function..."
        }
    ]
}
```

#### Error Response

```json
{
    "detail": "Internal Server Error"
}
``` 
