# demo-webapp

## Local developpment Setup Instructions
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
Before proceeding, create a `.env` file in the root directory of the project or define the environment variables directly. Use the `.env.example` file as a reference for the required variables:

#### Chatbot Integration
To enable the chatbot, you must set the following Azure AI Foundry variables in your `.env` file:

```
AZURE_FOUNDRY_ENDPOINT=<your-azure-endpoint>
AZURE_FOUNDRY_KEY=<your-azure-key>
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

By default, the environment variables will take priority, and if none are defined, the ones defined in the `.venv` file under the root folder of the application will be used.

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
