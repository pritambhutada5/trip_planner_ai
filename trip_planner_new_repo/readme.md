***

# AI Trip Planner with Retrieval-Augmented Generation (RAG)

This repository contains the source code for a production-ready, AI-powered Trip Planner. It leverages a Retrieval-Augmented Generation (RAG) pipeline to create highly personalized and factually-grounded travel itineraries. The application is built with a modern Python stack and 
deployed as a multi-container application using Docker and Docker Compose.

## ✨ Features

*   **Intelligent Itinerary Generation:** Creates detailed, day-by-day travel plans based on user-provided destination, dates, and preferences.
*   **Retrieval-Augmented Generation (RAG):** Enhances LLM responses by grounding them in factual data from user-provided documents, using `sentence-transformers` for embeddings and `FAISS` for fast vector search.
*   **Decoupled Architecture:** A robust **FastAPI** backend serves the AI logic, while a polished **Streamlit** frontend provides an interactive user experience.
*   **Professional UI/UX:** A clean, dark-themed interface with nested accordion-style expanders for a clear and organized presentation of hotels, restaurants, and daily itineraries.
*   **Defensive AI Implementation:** The backend includes robust post-processing and sanitization layers to correct for common LLM issues like data hallucinations and malformed URLs.
*   **Production-Ready Deployment:** The entire application is containerized with **Docker** and orchestrated with **Docker Compose**, featuring a health-check-based startup sequence to ensure stability.

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

*   You must have **Docker** and **Docker Compose** installed on your system.
*   An optional, but recommended, tool is a `.env` file in the root directory to store your `GEMINI_API_KEY`.

### Quick Start with Docker (Recommended)

This is the fastest and most reliable way to run the application.

1.  **Clone the Repository**
    ```sh
    git clone [your-repository-url]
    cd [your-repository-name]
    ```

2.  **Create an Environment File**
    Create a file named `.env` in the root of the project and add your API key:
    ```
    GEMINI_API_KEY="your_google_api_key_here"
    ```

3.  **Build and Run with Docker Compose**
    This single command will build the images, create the network, and start both the backend and frontend containers in the correct order.
    ```sh
    docker-compose up --build
    ```

4.  **Access the Application**
    *   **Frontend UI:** Open your browser and navigate to `http://localhost:8501`
    *   **Backend API Docs:** You can view the automatically generated API documentation at `http://localhost:8000/docs`

## ⚙️ Project Structure

```
.
├── .streamlit/
│   └── config.toml      # Streamlit theme configuration
├── api_routes.py        # Defines the FastAPI API routes
├── Dockerfile           # Instructions to build the application container
├── docker-compose.yml   # Orchestrates the backend and frontend services
├── requirements.txt     # Python dependencies
├── single_main.py       # FastAPI application entrypoint and health check
├── single_trip_agent.py # Core AI logic, RAG pipeline, and LLM communication
└── streamlit_app.py     # The Streamlit frontend application code
```

## 🧠 Advanced Concepts Implemented

This project is more than a simple script; it's a demonstration of building a real-world AI application. Key advanced concepts include:
*   **RAG for Factual Grounding:** Prevents LLM hallucinations by providing relevant, factual context in every prompt.
*   **Container Health Checks:** The `docker-compose.yml` uses a `/health` endpoint in the backend to guarantee the frontend doesn't start until the AI models are loaded and the API is ready.
*   **Defensive Post-Processing:** The backend sanitizes all LLM outputs (e.g., fixing malformed URLs) to ensure data integrity and prevent the UI from breaking.
*   **Optimized Docker Builds:** The `Dockerfile` is structured to leverage layer caching and BuildKit's cache mounts, dramatically reducing rebuild times during development.
*   **Docker Networking:** The frontend and backend containers communicate seamlessly over a private Docker network using service names (`http://backend:8000`), a best practice for microservice architectures.

## 🔮 Future Work

This project provides a solid foundation for many exciting future enhancements:
*   [ ] **User Accounts:** To save and manage past and future trips.
*   [ ] **Interactive Editing:** Allow users to drag-and-drop or regenerate specific parts of their itinerary.
*   [ ] **Real-Time Data:** Integrate live APIs for weather forecasts, flight prices, and local events.
*   [ ] **Cloud Deployment:** Deploy the containerized application to a cloud platform like AWS ECS or Google Cloud Run for public access.
