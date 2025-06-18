# Gemini Fullstack LangGraph Quickstart

This project demonstrates a fullstack application using a React frontend and a LangGraph-powered backend agent. The agent is designed to perform comprehensive research on a user's query by dynamically generating search terms, querying the web using Google Search, reflecting on the results to identify knowledge gaps, and iteratively refining its search until it can provide a well-supported answer with citations. This application serves as an example of building research-augmented conversational AI using LangGraph and Google's Gemini models.

![Gemini Fullstack LangGraph](./app.png)

## Features

- 💬 Fullstack application with a React frontend and LangGraph backend.
- 🧠 Powered by a LangGraph agent for advanced research and conversational AI.
- 🔍 Dynamic search query generation using Google Gemini models.
- 🌐 Integrated web research via Google Search API.
- 🤔 Reflective reasoning to identify knowledge gaps and refine searches.
- 📄 Generates answers with citations from gathered sources.
- 🔄 Hot-reloading for both frontend and backend development during development.
- 🔥 **Firebase Authentication**: Secures backend routes, requiring a Firebase ID token.
- 📚 **RAG with Google Cloud Storage & Vertex AI**: Ingests documents from GCS for Retrieval Augmented Generation, using Vertex AI for embeddings.
- ☁️ **CI/CD with Cloud Build**: Automated testing, building, and deployment of Docker images to Google Artifact Registry.

## Project Structure

The project is divided into two main directories:

-   `frontend/`: Contains the React application built with Vite.
-   `backend/`: Contains the LangGraph/FastAPI application, including the research agent logic.

## Getting Started: Development and Local Testing

Follow these steps to get the application running locally for development and testing.

**1. Prerequisites:**

-   Node.js and npm (or yarn/pnpm)
-   Python 3.11+
-   Google Cloud SDK (gcloud CLI) authenticated to your GCP account.

**2. Google Cloud Project Setup:**

-   **Create or select a GCP Project:** You'll need an active Google Cloud Project.
-   **Enable APIs:** Ensure the following APIs are enabled for your project:
    *   Secret Manager API
    *   Vertex AI API
    *   Cloud Storage API
    *   Firebase (Set up a Firebase project and link it to your GCP project. Enable Firebase Authentication.)
    *   Artifact Registry API (if you intend to use Cloud Build to push images there)
-   **Service Account:**
    *   Create a service account in your GCP project.
    *   Download its JSON key file.
    *   Grant the following IAM roles to this service account (or a principal running the application):
        *   `Secret Manager Secret Accessor` (to access the Gemini API Key)
        *   `Vertex AI User` (to use Vertex AI embedding models)
        *   `Storage Object Admin` or `Storage Object Viewer` (on the RAG GCS bucket, depending on if it needs to write or just read)
        *   Firebase related roles (e.g., `Firebase Admin SDK Administrator Service Agent` - consult Firebase documentation for minimal roles needed by Firebase Admin SDK).
-   **Set `GOOGLE_APPLICATION_CREDENTIALS`:**
    *   In your local development environment, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the downloaded service account JSON key file.
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
    ```
    *   When deployed to GCP environments (e.g., Cloud Run, GKE), this is often handled automatically by Application Default Credentials (ADC).

**3. Environment Variable Configuration (`backend/.env`):**

The backend relies on several environment variables. Navigate to the `backend/` directory, copy `backend/.env.example` to a new file named `.env`, and configure it:

-   **`GCP_PROJECT_ID`**: Your Google Cloud Project ID.
-   **`GCP_LOCATION`**: The GCP region for Vertex AI services (e.g., `us-central1`).
-   **`GEMINI_API_KEY_SECRET_ID`**: The ID of the secret in Secret Manager that stores your Gemini API Key. The actual Gemini API Key should be stored as a secret value in Secret Manager.
    *   _Previously, `GEMINI_API_KEY` was set directly. It's now fetched from Secret Manager._
-   **`EMBEDDING_MODEL_NAME`**: The Vertex AI embedding model to use (e.g., `textembedding-gecko@001`).
-   **`RAG_GCS_BUCKET_NAME`**: The name of the Google Cloud Storage bucket where documents for RAG will be stored.
-   **`GOOGLE_APPLICATION_CREDENTIALS`**: (Handled as per step 2.4, no need to set its value directly in the `.env` file if the environment variable is already set).
-   Other variables like `POSTGRES_USER`, `POSTGRES_PASSWORD`, etc., should be configured as per their descriptions in `.env.example` if you are using the local Docker Compose setup for Postgres.

**4. Install Dependencies:**

**Backend:**

```bash
cd backend
pip install .
```

**Frontend:**

```bash
cd frontend
npm install
```

**3. Run Development Servers:**

**Backend & Frontend (using Makefile in project root):**

```bash
make dev
```
This will run the backend and frontend development servers. Open your browser and navigate to the frontend development server URL (e.g., `http://localhost:5173/app`).

_Alternatively, you can run the backend and frontend development servers separately. For the backend, open a terminal in the `backend/` directory and run `langgraph dev`. The backend API will be available at `http://127.0.0.1:2024`. It will also open a browser window to the LangGraph UI. For the frontend, open a terminal in the `frontend/` directory and run `npm run dev`. The frontend will be available at `http://localhost:5173`._

## How the Backend Agent Works (High-Level)

The core of the backend is a LangGraph agent defined in `backend/src/agent/graph.py`. It follows these steps:

![Agent Flow](./agent.png)

1.  **Generate Initial Queries:** Based on your input, it generates a set of initial search queries using a Gemini model.
2.  **Web Research:** For each query, it uses the Gemini model with the Google Search API to find relevant web pages.
3.  **Reflection & Knowledge Gap Analysis:** The agent analyzes the search results to determine if the information is sufficient or if there are knowledge gaps. It uses a Gemini model for this reflection process.
4.  **Iterative Refinement:** If gaps are found or the information is insufficient, it generates follow-up queries and repeats the web research and reflection steps (up to a configured maximum number of loops).
5.  **RAG from GCS (if applicable):** If the agent determines it needs to use local documents (a capability triggered by `use_documents: true` in the input state), it can load and process PDF documents from the GCS bucket specified by `RAG_GCS_BUCKET_NAME`. These documents are chunked, and embeddings are generated using Vertex AI (`EMBEDDING_MODEL_NAME`). The resulting vectors are stored for similarity search.
6.  **Finalize Answer:** Once the research is deemed sufficient (from web search and/or RAG), the agent synthesizes the gathered information into a coherent answer, including citations, using a Gemini model.

## Firebase Authentication

The backend has Firebase Authentication integrated.
-   Protected routes (e.g., `/api/v1/documents/`) require a valid Firebase ID token to be passed in the `Authorization: Bearer <ID_TOKEN>` header.
-   The frontend application will need to implement Firebase sign-in flows (e.g., using Firebase SDK for JavaScript) to obtain this ID token and include it in requests to secured backend endpoints. Consult the [Firebase Authentication Documentation](https://firebase.google.com/docs/auth/web/start) for client-side setup.

## CI/CD with Cloud Build

This project includes a `cloudbuild.yaml` file to enable Continuous Integration and Continuous Deployment using Google Cloud Build.
-   **Automated Testing:** The Cloud Build pipeline automatically installs backend dependencies and runs backend tests (`pytest`). Frontend tests can be added if implemented.
-   **Docker Image Build:** It builds a Docker image using the provided `Dockerfile`.
-   **Artifact Registry:** The built Docker image is pushed to Google Artifact Registry, tagged with `latest` and the commit SHA.
This setup facilitates automated deployments to services like Cloud Run or Google Kubernetes Engine.

## Deployment

The primary method for deployment is now via Docker images built by Cloud Build and stored in Artifact Registry.

**1. Build and Push Docker Image (CI/CD):**
   The `cloudbuild.yaml` configuration handles this automatically when connected to a Git repository trigger in Cloud Build.

**2. Running Locally with Docker (for testing the production image):**
   If you wish to run the production-like Docker image locally (after it has been built, e.g., by Cloud Build and pulled, or built locally using `docker build`):
   ```bash
   # Example: docker pull us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gemini-fullstack-app/app:latest
   # Then run, ensuring all necessary environment variables are set:
   docker run -p 8080:2024 \
     -e GCP_PROJECT_ID="your-gcp-project-id" \
     -e GCP_LOCATION="us-central1" \
     -e GEMINI_API_KEY_SECRET_ID="your-gemini-secret-id" \
     -e EMBEDDING_MODEL_NAME="textembedding-gecko@001" \
     -e RAG_GCS_BUCKET_NAME="your-rag-bucket-name" \
     -e GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/gcp-key.json" \ # If mounting a key into the container
     # Add other necessary env vars like DATABASE_URL if not using default local/testing setup
     us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gemini-fullstack-app/app:latest
   ```
   *Note: The port inside the container is `2024` (FastAPI default when run with `langgraph dev` or similar). The `-p 8080:2024` maps port 8080 on your host to 2024 in the container. Adjust as needed.*
   *The `Dockerfile` is based on `langchain/langgraph-api` which might have specific expectations for how it's run. The `ENV LANGGRAPH_HTTP` in the Dockerfile points to `backend/src/agent/app.py:app`.*

   The old `docker-compose.yml` might still be useful for spinning up local Postgres/Redis but would need updates to use the new environment variable scheme and potentially build the image using the local Dockerfile directly if not pulling from Artifact Registry.

## Technologies Used

- [React](https://reactjs.org/) (with [Vite](https://vitejs.dev/)) - For the frontend user interface.
- [Tailwind CSS](https://tailwindcss.com/) - For styling.
- [Shadcn UI](https://ui.shadcn.com/) - For components.
- [LangGraph](https://github.com/langchain-ai/langgraph) - For building the backend research agent.
- [Google Gemini](https://ai.google.dev/models/gemini) - LLM for query generation, reflection, and answer synthesis.
- **Google Cloud Platform**:
    - Firebase (Authentication)
    - Secret Manager (API Key Management)
    - Vertex AI (Embeddings)
    - Cloud Storage (RAG Document Store)
    - Cloud Build (CI/CD)
    - Artifact Registry (Docker Image Storage)
- FastAPI - Backend web framework.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details. 