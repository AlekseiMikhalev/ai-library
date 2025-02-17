# **Non-Fiction AI Library**

## **Project Overview**  

The Non-Fiction AI Library is an advanced tool designed for extracting and organizing knowledge from PDF documents. It enables users to upload PDFs, extract structured features, cluster related sections, and use a **Graph RAG** to learn knowledge concepts. The project leverages **Python**, **FastAPI**, and several key technologies, including **LLMSherpa, MongoDB (pymongo, motor), Neo4j, Ollama, and scikit-learn**.  

Users can interact with the system to:  
- Extract structured knowledge from PDFs.  
- Build a knowledge graph using **Neo4j**.  
- Query the graph for relevant books, chapters, and knowledge concepts.  
- Retrieve and generate insights using **LLMs**.  

## **Technology Stack**  

- **Backend:** FastAPI, LLMSherpa, MongoDB (Motor), Neo4j, Ollama, scikit-learn  
- **Frontend:** Next.js  
- **Database:** MongoDB (for document storage), Neo4j (for knowledge graph)  
- **AI & ML:** LLMSherpa for text extraction, scikit-learn for clustering  
- **Containerization:** Docker, Docker Compose  
- **Authentication & Security:** To be implemented  

## **Development Roadmap**  

The project is in the early development phase and follows an iterative roadmap:  

### **Phase 1: Core Feature Development**  
✅ Backend module for **PDF upload and feature extraction**  
✅ Backend module for **clustering extracted text sections**  
🔲 Backend module for **building the knowledge graph (Neo4j)**  
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

```
📂 api/                # Backend FastAPI application  
   ├── main.py         # API entry point  
   ├── routers/        # API routes  
   ├── services/       # Business logic and feature extraction  
   ├── repository/     # Database interaction (MongoDB, Neo4j)  
📂 frontend/           # Next.js frontend  
📄 docker-compose.yml  # Development & testing environment  
📄 example.env         # Example environment variables  
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