# demo-webapp

## Project Goal and Disclaimer

This is a custom application built to serve multiple purposes:

- **Demonstrate Application Modernization Journey**
- **Showcase Integrations with Azure Services** such as AKS, Container App, Application Insights, Azure AI Foundry, Azure Database for PostgreSQL Flexible Server, Azure Monitor, and more.

> **Disclaimer:** This is not an official Microsoft repository. It is my own repository, created for demonstration and educational purposes.

## Local Development Setup Instructions
<details>

### 1. Create a Virtual Environment

First, create a virtual environment to isolate the project's dependencies:

```bash
python3 -m venv venv
```

### 2. Activate the Virtual Environment

Activate the virtual environment using the following command:

- On Windows:
  ```bash
  venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```
### 3. Configure Environment Variables
Before proceeding, create a `.env` file in the root directory of the project or define the environment variables directly. Use the `.env.example` file as a reference for the required variables.

#### Azure Identity Setup
To enable Azure authentication, you must set the following variables in your environment (or provide them via Key Vault in production):

```
AZURE_CLIENT_ID=<your-azure-client-id>
AZURE_TENANT_ID=<your-azure-tenant-id>
AZURE_CLIENT_SECRET=<your-azure-client-secret>
```

These are now managed via Azure Key Vault in Kubernetes deployments. Make sure your Key Vault contains these secrets and your cluster is configured to access them.

#### Chatbot Integration
To enable the chatbot, you must set the following Azure AI Foundry variables in your `.env` file:

```
AZURE_FOUNDRY_ENDPOINT=<your-azure-endpoint>
AZURE_FOUNDRY_AGENT_ID=<your-agent-id>
```

If these are not set, the chatbot UI will be disabled and a warning will be shown.

**Azure AI Foundry Setup Requirements:**

To have the chatbot working, you must configure Azure AI Foundry as follows:

1. **Azure AI Foundry Project**: Create a project in Azure AI Foundry.
2. **Agent Creation**: Create an agent within your Azure AI Foundry project.
3. **Agent Action (OpenAPI 3.0)**: Add an action to your agent of kind `OpenAPI 3.0`. For this action:
    - Upload the `openapi-3.0.json` file from this repository.
    - Ensure you specify the correct URL of your application frontend in the OpenAPI action configuration. This is required so the agent can make API requests to your app backend.

If any of these steps are not completed, the chatbot will not function.

---

### Test Your Azure AI Foundry Connection

To verify your Azure AI Foundry integration is working, you can run the following Python script:

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Load environment variables
endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT")
agent_id = os.getenv("AZURE_FOUNDRY_AGENT_ID")

# Initialize client
client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

# Create thread and send message
thread = client.agents.threads.create()
client.agents.messages.create(thread_id=thread.id, role="user", content="Hello, create a task name test task for the project Apollo.")
run = client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent_id)

# Check run status
if run.status == "failed":
    print("❌ Agent run failed:", run.last_error)
else:
    messages = client.agents.messages.list(thread_id=thread.id)
    for msg in messages:
        if msg.role == "assistant":
            print("✅ Agent response:", msg.text_messages[-1].text.value)
```

If you see a response from the agent, your connection is successful. If you see an error, check your environment variables and Azure configuration.

### 4. Install Dependencies

Install the required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### 5. Run a Local PostgreSQL Server (Development Only)

To run a local PostgreSQL server for development, use the following command:

```bash
docker run -p 5432:5432 --name postgres --network podman -e POSTGRES_PASSWORD=mypassword -d postgres:16.8
```

To refresh the PostgreSQL server, execute the following commands:

```bash
docker stop postgres
docker rm postgres
docker run -p 5432:5432 --name postgres --network podman -e POSTGRES_PASSWORD=mypassword -d postgres:16.8
```

### 6. Run the Server

Before running the server, apply the migrations:

```bash
python manage.py makemigrations tasks
python manage.py migrate
```

Run the Django development server:

```bash
python manage.py runserver
```

The server will start, and you can access the application at `http://127.0.0.1:8000/`.

### 7. Additional Commands

- To apply migrations:
  ```bash
  python manage.py migrate
  ```

- To create a superuser:
  ```bash
  python manage.py createsuperuser
  ```

- To collect static files:
  ```bash
  python manage.py collectstatic
  ```
</details>

## Generate a docker image
<details>

### Build Docker Image

To build the Docker image for the application, use the following command:

```bash
docker build -t demo-webapp:latest .
```

### Tag and Push Docker Image

To tag the Docker image and push it to a registry, use the following commands:

```bash
docker tag demo-webapp:latest your-registry/demo-webapp:latest
docker push your-registry/demo-webapp:latest
```

Replace `your-registry` with the actual registry URL.

### Run Docker Container

To run the Docker container, use the following command:

```bash
docker run -p 8000:8000 --network podman demo-webapp:latest
```

To run the container in detached mode, add the `-d` flag:

```bash
docker run -d -p 8000:8000 --network podman demo-webapp:latest
```

To run the Docker container with environment variables, use the following command:

```bash
docker run -d -p 8000:8000 --network podman \
  -e DB_USER=postgres \
  -e DB_PASSWORD=your-db-password \
  -e DB_NAME=postgres \
  -e DB_HOST=localhost \
  -e DB_PORT=5432 \
  demo-webapp:latest
```
</details>

### (Optional) Populate dummy data
Execute the following command to populate dummy users, projects, and random tasks in the database:

```bash
./manage.py populate_dummy_data
```

By default, this will create 5 users, 5 projects, and 50 tasks. To specify a different number of tasks, use the `--count` parameter:

```bash
./manage.py populate_dummy_data --count 100
```

Replace `100` with the desired number of tasks to create. The users and projects will always be 5 each.

## Logger Test Page

A logger test page is available at `/logger/`. When you visit this page in your browser, it will:

- Trigger a Django log entry with the message `Logger is working!` (visible in your server logs)
- Display a confirmation web page

This is useful for verifying that Django logging is working correctly in your environment. Check your server logs after visiting `/logger/` to confirm the log entry appears.

Make sure to follow these steps to set up and run the demo-webapp successfully.
