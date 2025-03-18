# **Non-Fiction AI Library**

## **Project Overview**  

The Non-Fiction AI Library is an advanced tool designed for extracting and organizing knowledge from PDF documents. It enables users to upload PDFs, extract structured features, and use a **Graph RAG** to learn knowledge concepts. The project leverages **Python**, **FastAPI**, and several key technologies, including **LLMSherpa, MongoDB (pymongo, motor), Neo4j, Ollama, and scikit-learn**.  

Users can interact with the system to:  
- Extract structured knowledge from PDFs.  
- Build a knowledge graph using **Neo4j**.  
- Query the graph for relevant books, chapters, and knowledge concepts.  
- Retrieve and generate insights using **LLMs**.  

## **Technology Stack**  

- **Backend:** FastAPI, LLMSherpa, MongoDB (Motor), Neo4j, Ollama, scikit-learn  
- **Frontend:** Next.js  
- **Database:** MongoDB (for document storage), Neo4j (for knowledge graph)  
- **AI & ML:** LLMSherpa for text extraction, Ollama for embeddings and generation 
- **Containerization:** Docker, Docker Compose  
- **Authentication & Security:** To be implemented  

## **Development Roadmap**  

The project is in the early development phase and follows an iterative roadmap:  

### **Phase 1: Core Feature Development**  
✅ Backend module for **PDF upload and feature extraction**  
✅ Backend module for **building the knowledge graph (Neo4j)**  
🔲 Backend module for **querying the knowledge graph using Cypher**  

### **Phase 2: User Interface & Interaction**  
🔲 Frontend module for **PDF upload & display**  
🔲 Frontend module for **querying knowledge concepts, LLM chat & visualizing the knowledge graph**  
🔲 Implement authentication and authorization  

### **Phase 3: Optimization & Production Readiness**  
🔲 Enhance **query performance and caching**  
🔲 Implement **task queues**  
🔲 Improve **scalability & security for production deployment**  
🔲 Deploy a **fully containerized system with optimized networking**  

## **Project Structure**  

The repository is structured as follows:  

```python
ai-library/
├── README.md             # Project documentation and overview
├── api/                  # API-related code and configurations
│   ├── .dockerignore     # Files to ignore in Docker builds
│   ├── .env              # Environment variables for development
│   ├── Dockerfile        # Instructions for building the Docker image
│   ├── Makefile          # Commands for building and managing the project
│   ├── docker-compose.dev.yml # Configuration for Docker Compose in development
│   ├── example.env       # Example environment variables
│   ├── pyproject.toml    # Project metadata and dependencies for Python
│   ├── pytest.ini        # Configuration for pytest
│   ├── src/              # Source code for the API
│   │   ├── __init__.py   # Marks the directory as a Python package
│   │   ├── config/       # Configuration files for the application
│   │   ├── database/     # Database models and migrations
│   │   ├── docs/         # Documentation files
│   │   ├── main.py       # Main entry point for the API
│   │   ├── models/       # Data models for the application
│   │   ├── pdf_uploads/  # Directory for uploaded PDF files
│   │   ├── repository/    # Data access layer for database interactions
│   │   ├── routers/      # API route definitions
│   │   ├── schemas/      # Data validation schemas
│   │   ├── services/     # Business logic of the application
│   │   ├── tasks.py      # Background tasks
│   │   ├── utils/        # Utility functions and helpers
│   │   ├── worker.py     # Worker for background processing
│   ├── tests/            # Test cases for the API
├── frontend/             # Frontend application code
```

## **Key Features**  

- **Intelligent PDF feature extraction** using **LLMSherpa**  
- **Automated clustering** of similar content with **scikit-learn**  
- **Knowledge graph construction** with **Neo4j**  
- **Graph-based retrieval** using Cypher queries  
- **FastAPI backend** with structured API routes  
- **Asynchronous processing** with `asyncio`  
- **Modern frontend** powered by **Next.js**   

### **Production Considerations**  

For a production-grade deployment, it is recommended to:  
- Deploy **each service in a separate container** for scalability.  
- Use **managed database services** for MongoDB and Neo4j.  
- Secure **authentication & authorization mechanisms**.  
- Implement **monitoring, and fault tolerance**.  
- Replace local PDF file storage to AWS S3

## **How to Run Locally**  

1. **Clone the repository:**  

   ```sh
   git clone https://github.com/AlekseiMikhalev/ai-library.git
   cd ai-library
   ```

2. **Set up environment variables:**  
   - Copy `example.env` to `.env` and configure necessary variables.  

3. **Start the development environment:**  

   ```sh
   make start-dev
   ```

4. **Access the services:**  
   - **API**: `http://localhost:8000/docs`  
   - **Frontend**: `http://localhost:3000`  
   - **Neo4j Browser**: `http://localhost:7474`  
   - **MongoDB Compass**: `http://localhost:27017`