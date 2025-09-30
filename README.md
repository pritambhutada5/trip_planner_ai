# AI Trip Planner with Retrieval-Augmented Generation (RAG)

This repository contains the source code for a production-ready, AI-powered Trip Planner. 
It leverages a Retrieval-Augmented Generation (RAG) pipeline to create highly personalized and factually-grounded travel itineraries. 
The application is built with a modern Python stack and deployed as a multi-container application using Docker and Docker Compose.

## ⚙️ Project Structure
```
.
├── .streamlit/
│   └── config.toml      # Streamlit theme configuration
├── knowledge_base/      # Folder for your source documents (PDFs, TXT, etc.)
├── faiss_store/         # Generated FAISS vector store
├── logs/                # Application log files (ignored by git)
├── api_routes.py        # Defines the FastAPI API routes
├── Dockerfile           # Instructions to build the application container
├── docker-compose.yml   # Orchestrates the backend and frontend services
├── logging_config.py    # Centralized logging configuration
├── rag_processor.py     # Script to build the FAISS vector store
├── requirements.txt     # Python dependencies
├── single_main.py       # FastAPI application entrypoint and health check
├── single_trip_agent.py # Core AI logic, RAG pipeline, and LLM communication
└── streamlit_app.py     # The Streamlit frontend application code
```

## ✨ Features

*   **Intelligent Itinerary Generation:** Creates detailed, day-by-day travel plans based on user-provided destination, dates, and preferences.
*   **Retrieval-Augmented Generation (RAG):** Enhances LLM responses by grounding them in factual data from user-provided documents, using `sentence-transformers` for embeddings and `FAISS` for fast vector search.
*   **Intelligent Fallback System:** If no relevant documents are found in the knowledge base, the system gracefully falls back to using the LLM's general knowledge to fulfill the user's request.
*   **Decoupled Architecture:** A robust **FastAPI** backend serves the AI logic, while a polished **Streamlit** frontend provides an interactive user experience.
*   **Defensive AI Implementation:** The backend includes robust post-processing and sanitization layers to correct for common LLM issues like data hallucinations and malformed URLs.
*   **Production-Ready Deployment:** The entire application is containerized with **Docker** and orchestrated with **Docker Compose**, featuring a health-check-based startup sequence to ensure stability.

## 🧠 RAG Implementation: In-Depth

The core intelligence of this application comes from its dynamic RAG pipeline, which decides whether to use custom knowledge or the LLM's general knowledge.

### 1. RAG Path (High-Relevance Documents Found)
When a user requests a trip plan, the system first performs a similarity search against the vector store (created from your documents in the `knowledge_base` folder).

*   If documents are found with a relevance score **above** the `RELEVANCE_THRESHOLD` (e.g., `0.4`), their content is extracted.
*   This retrieved context is then injected directly into the prompt sent to the LLM.
*   The LLM is explicitly instructed to **base its response ONLY on the provided context**, ensuring the trip plan is grounded in your specific documents. This is ideal for creating a plan based on a custom travel guide for a specific location like Tokyo.

### 2. General Knowledge Fallback Path (No Relevant Documents)
If the similarity search yields no documents above the `RELEVANCE_THRESHOLD`, the system intelligently switches to a fallback mode.

*   The backend recognizes that there is no relevant custom knowledge to use.
*   It constructs a **different prompt** that instructs the LLM to ignore any previous context and generate a trip plan from scratch using its general knowledge.
*   This ensures the user still receives a high-quality itinerary for any destination, even if it's not covered by the documents in the `knowledge_base`.

This dual-path system makes the application both powerful when custom knowledge is available and robustly versatile when it is not.

## 🚀 Getting Started and Testing RAG

Follow these instructions to get the project running locally and test the RAG functionality.

### Prerequisites

*   You must have **Docker** and **Docker Compose** installed on your system.
*   A Python environment (3.10+) is required to run the pre-processing script.

### Local Development Setup

1.  **Clone the Repository**
    ```sh
    git clone https://github.com/pritambhutada5/trip_planner_ai.git
    cd trip_planner_ai/trip_planner_new_repo
    ```

2.  **Create an Environment File**
    Create a file named `.env` in the `trip_planner_new_repo` directory and add your API key:
    ```
    GEMINI_API_KEY="your_google_api_key_here"
    ```

3.  **Set up Virtual Environment and Install Dependencies**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

4.  **Create the Knowledge Base (Crucial Step)**
    *   Create a folder named `knowledge_base` inside the `trip_planner_new_repo` directory.
    *   **To test the RAG path:** Place documents related to a specific destination (e.g., a PDF guide to Tokyo) into this folder.
    *   **To test the fallback path:** Leave this folder empty.

5.  **Generate the Vector Store**
    You must run this script to process your documents and build the vector store that the backend depends on.
    ```sh
    python rag_processor.py
    ```
    Re-run this step whenever you change the contents of the `knowledge_base` directory.

6.  **Build and Run with Docker Compose**
    ```sh
    docker-compose up --build
    ```

7.  **Test the RAG Logic**
    *   **Test the RAG Path:** On the UI, enter a destination that matches your documents (e.g., "Tokyo, Japan"). Check the backend logs in your terminal. You should see `INFO` messages about relevant sources being found and `DEBUG` messages showing the retrieval scores.
    *   **Test the Fallback Path:** Enter a destination that is *not* in your documents (e.g., "Paris, France"). The logs should show `INFO: No relevant context found...`, and the AI will generate a plan from its general knowledge.



## 🔮 Future Work

This project provides a solid foundation for many exciting future enhancements:
*   **User Accounts:** To save and manage past and future trips.
*   **Interactive Editing:** Allow users to drag-and-drop or regenerate specific parts of their itinerary.
*   **Real-Time Data:** Integrate live APIs for weather forecasts, flight prices, and local events.
*   **Cloud Deployment:** Deploy the containerized application to a cloud platform like Render, AWS, or Google Cloud.
