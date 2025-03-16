# Kubernetes Cluster Doctor Bridge

A Python-based bridge service that connects your Kubernetes cluster data (logs, events, pod descriptions, service info, etc.) to an LLM (e.g., Ollama Llama 3.2) via a chat interface. This project enables real-time, guided troubleshooting and diagnosis of cluster issues.

## Overview

The Cluster Doctor Bridge provides a RESTful API that:
- Fetches logs for specified pods.
- Retrieves detailed descriptions of pods.
- Gets cluster events and service details.
- Processes and formats data for integration with an LLM chat UI.
- Maintains conversational context for interactive debugging sessions.

## File Structure

- **main.py**:  
  Entry point that starts the FastAPI web server and registers API routes.
- **config.py**:  
  Contains configuration settings (server host/port, Kubernetes defaults, log chunk size, etc.).
- **handlers.py**:  
  Defines API endpoints (`/get-logs`, `/describe-pod`, `/get-events`, `/get-svc`) that clients (or an LLM chat UI) use to request Kubernetes data.
- **kubectl_utils.py**:  
  Provides functions to run `kubectl` commands (or use the Kubernetes API) for fetching logs, pod descriptions, events, and service information.
- **models.py**:  
  Defines data models (using Pydantic) for standardizing API responses (logs, pod description, events, service info).
- **utils.py**:  
  Contains helper functions for processing data (e.g., splitting large logs into chunks, masking sensitive data, summarizing output).

## Prerequisites

- **Python 3.8+**  
- **FastAPI** and **uvicorn** (for the web server)  
- **kubectl** installed and configured (with access to your Kubernetes cluster)  
- Optionally, install the Kubernetes Python client if you wish to integrate directly with the cluster via API.

## Setup Instructions

1. **Clone the Repository:**

   ```bash
   git clone <your-repository-url>
   cd <repository-folder>
   ```

2. **Create and Activate a Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install fastapi uvicorn pydantic
   # Optionally, install the Kubernetes Python client:
   # pip install kubernetes
   ```

4. **Configure Your Environment:**

   - Edit `config.py` if necessary to update the server host, port, or default Kubernetes settings.

5. **Run the Bridge Service:**

   ```bash
   python main.py
   ```

   The API server will start and listen on the configured host and port (default: http://127.0.0.1:8000).

## API Endpoints

The service exposes several endpoints under the `/api` prefix:

- **GET `/api/get-logs`**  
  - **Parameters:** `pod_name` (required), `namespace` (optional), `since_time` (optional), `tail_lines` (optional)  
  - **Description:** Returns logs for the specified pod in manageable chunks.

- **GET `/api/describe-pod`**  
  - **Parameters:** `pod_name` (required), `namespace` (optional)  
  - **Description:** Provides detailed output from `kubectl describe pod`.

- **GET `/api/get-events`**  
  - **Parameters:** `namespace` (optional), `since_time` (optional)  
  - **Description:** Retrieves recent events for the specified namespace.

- **GET `/api/get-svc`**  
  - **Parameters:** `service_name` (required), `namespace` (optional)  
  - **Description:** Returns service details in YAML format.

## Integration with LLM Chat UI

The intended integration workflow is as follows:

1. **Chat UI/LLM Interaction:**  
   Your chat interface sends requests to the bridge endpoints when the LLM asks for specific cluster data (e.g., logs or events).

2. **Bridge Service:**  
   Processes the request, executes the necessary `kubectl` commands (or Kubernetes API calls), and returns formatted JSON responses.

3. **Conversational Context:**  
   The LLM uses the structured responses along with conversation memory to diagnose issues and ask follow-up questions.

4. **Feedback Loop:**  
   The LLM can guide you by asking for additional details (e.g., “Please show me the last 50 lines of logs for pod X”), and the chat UI will fetch new data from the bridge service.

## Troubleshooting & Next Steps

- **Ensure `kubectl` is configured correctly** to access your cluster.
- **Test endpoints using a tool like `curl` or Postman** to validate API responses.
- **Review logs and API responses** for any errors and adjust configurations as needed.
- Use the documented endpoints and structured JSON responses to further refine your LLM’s ability to diagnose cluster issues.