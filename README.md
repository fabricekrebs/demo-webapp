# demo-webapp

## Setup Instructions

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

### 3. Install Dependencies

Install the required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### 4. Run the Server

Run the Django development server:

```bash
python manage.py runserver
```

The server will start, and you can access the application at `http://127.0.0.1:8000/`.

### 5. Additional Commands

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

### 6. Build Docker Image

To build the Docker image for the application, use the following command:

```bash
docker build -t demo-webapp:latest .
```

### 7. Tag and Push Docker Image

To tag the Docker image and push it to a registry, use the following commands:

```bash
docker tag demo-webapp:latest your-registry/demo-webapp:latest
docker push your-registry/demo-webapp:latest
```

Replace `your-registry` with the actual registry URL.

### 8. Run Docker Container

To run the Docker container, use the following command:

```bash
docker run -p 8000:8000 --network yournetwork demo-webapp:latest
```

To run the container in detached mode, add the `-d` flag:

```bash
docker run -d -p 8000:8000 --network yournetwork demo-webapp:latest
```

Make sure to follow these steps to set up and run the demo-webapp successfully.
