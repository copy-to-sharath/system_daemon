# Celery + Metaflow with Dynamic CPU-Based Scheduling

This guide provides step-by-step instructions to set up a Celery job that dynamically triggers tasks based on your system's CPU count and load. The tasks execute a simple Metaflow workflow and (optionally) send notifications to Microsoft Teams. In addition, you will learn how to monitor the system using Flower, Prometheus, and Grafana.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Setting Up Redis](#3-setting-up-redis)
4. [Creating Application Files](#4-creating-application-files)
    - [4.1. celery_app.py](#41-celery_apppy)
    - [4.2. tasks.py](#42-taskspy)
5. [Understanding `run_metaflow.delay()`](#5-understanding-run_metaflowdelay)
6. [Running the Application](#6-running-the-application)
7. [Monitoring with Flower](#7-monitoring-with-flower)
8. [Integrating with Microsoft Teams](#8-integrating-with-microsoft-teams)
9. [Monitoring with Prometheus and Grafana](#9-monitoring-with-prometheus-and-grafana)
10. [Final Notes](#10-final-notes)

## 1. Prerequisites

- **Python 3.7+**
- **Redis Server:** Either installed locally or running via Docker.
- Basic familiarity with **Celery**, **Metaflow**, and system monitoring using **psutil**.

## 2. Installation

Install the required Python packages using pip:

```bash
pip install celery redis metaflow flower requests psutil

Package Overview:

celery: Distributed task queue.
redis: Message broker for Celery.
metaflow: Framework to build and run workflows.
flower: Web-based tool for monitoring Celery tasks.
requests: For sending HTTP notifications (e.g., to Microsoft Teams).
psutil: For monitoring system metrics (e.g., CPU usage).

3. Setting Up Redis
Ensure Redis is running on your system.

Option 1: Local Installation
For Ubuntu/Debian:

sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server


For macOS (with Homebrew):

bash
Copy
Edit
brew install redis
redis-server /usr/local/etc/redis.conf
Option 2: Using Docker
bash
Copy
Edit
docker run -d --name redis -p 6379:6379 redis
4. Creating Application Files
Create the following two files in your project directory.

4.1. celery_app.py
This file sets up the Celery application with Redis as the broker and configures the beat scheduler to trigger a dynamic scheduler task every second.

python
Copy
Edit
from celery import Celery

# Create a Celery instance with Redis as both the broker and backend.
app = Celery('metaflow_celery',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

# Configure Celery Beat to run the dynamic scheduler task every second.
app.conf.beat_schedule = {
    'dynamic-scheduler-every-second': {
        'task': 'tasks.schedule_metaflow_tasks',
        'schedule': 1.0,  # Trigger every second
    },
}
app.conf.timezone = 'UTC'

if __name__ == '__main__':
    app.start()
4.2. tasks.py
This file contains the Metaflow workflow and Celery tasks. It includes a task to execute the workflow and a dynamic scheduler that checks CPU metrics to decide when to trigger the workflow tasks.

python
Copy
Edit
import os
import psutil
from celery_app import app
from metaflow import FlowSpec, step
import requests

# Sample Metaflow Workflow
class HelloFlow(FlowSpec):
    
    @step
    def start(self):
        print("Hello from Metaflow!")
        self.next(self.end)
    
    @step
    def end(self):
        print("Metaflow workflow finished.")

# Celery Task to run the Metaflow workflow
@app.task(name='tasks.run_metaflow')
def run_metaflow():
    try:
        # Run the Metaflow workflow
        flow = HelloFlow()
        flow.run()

        # Optionally, send a notification to Microsoft Teams
        teams_webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
        if teams_webhook_url:
            message = {
                "title": "Celery Task Notification",
                "text": "Metaflow workflow executed successfully."
            }
            response = requests.post(teams_webhook_url, json=message)
            print(f"Teams notification sent. Status code: {response.status_code}")
        else:
            print("TEAMS_WEBHOOK_URL not set. Skipping Teams notification.")
    except Exception as e:
        print(f"Error executing Metaflow workflow: {e}")

# Dynamic Scheduler Task:
# Checks current CPU load and, if under threshold, triggers tasks.
@app.task(name='tasks.schedule_metaflow_tasks')
def schedule_metaflow_tasks():
    # Get the total number of CPUs available
    cpu_count = os.cpu_count() or 1

    # Get current CPU usage percentage over a short interval
    cpu_usage = psutil.cpu_percent(interval=0.1)
    threshold = 70  # Define CPU usage threshold (in percent)

    print(f"CPU Count: {cpu_count}, CPU Usage: {cpu_usage}%")
    
    if cpu_usage < threshold:
        # Heuristic: schedule one task per CPU core if load is low.
        tasks_to_schedule = cpu_count
        print(f"Scheduling {tasks_to_schedule} run_metaflow tasks.")
        for _ in range(tasks_to_schedule):
            run_metaflow.delay()
    else:
        print("CPU usage too high; no tasks scheduled this cycle.")
5. Understanding run_metaflow.delay()
When you call run_metaflow.delay(), it enqueues the run_metaflow task for asynchronous execution. This call returns an AsyncResult object that you can use to track the task's progress and result.

Key Points:

Synchronous Execution:
Calling run_metaflow() directly executes the task immediately.

Asynchronous Execution:
run_metaflow.delay() sends a message to the Celery broker (Redis), where it is picked up by an available worker for processing.

Example:

python
Copy
Edit
result = run_metaflow.delay()
# 'result' is an AsyncResult instance that can be used to monitor the task.
6. Running the Application
Follow these steps to run the application:

Start Redis:
Ensure Redis is running (refer to Step 3: Setting Up Redis).

Start the Celery Worker with Beat Scheduler:
In your project directory, run:

bash
Copy
Edit
celery -A celery_app worker --beat --loglevel=info
This command starts both the Celery worker and the beat scheduler, which triggers the dynamic scheduler task every second.

Monitor the Logs:
Watch the terminal output to observe CPU metrics and task scheduling decisions.

7. Monitoring with Flower
Flower is a web-based UI that monitors your Celery tasks.

Start Flower:
Open a new terminal window and run:

bash
Copy
Edit
celery -A celery_app flower
Access Flower:
Open your web browser and navigate to http://localhost:5555 to view real-time task information.

8. Integrating with Microsoft Teams
Enable notifications for task completions via Microsoft Teams:

Create an Incoming Webhook:
In your Teams channel, add the Incoming Webhook connector and obtain the webhook URL.

Set the Environment Variable:
In your terminal, set the environment variable:

bash
Copy
Edit
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/your-webhook-url"
Test the Integration:
When a Metaflow task completes, a notification will be sent to your Teams channel.

9. Monitoring with Prometheus and Grafana
Celery does not directly expose metrics, but you can use a Celery exporter to integrate with Prometheus.

Install a Celery Exporter:
For example, install celery-exporter:

bash
Copy
Edit
pip install celery-exporter
Run the Exporter:
Launch the exporter to expose Celery metrics via an HTTP endpoint.

Configure Prometheus:
In your prometheus.yml configuration file, add a job for Celery:

yaml
Copy
Edit
scrape_configs:
  - job_name: 'celery'
    static_configs:
      - targets: ['localhost:YOUR_EXPORTER_PORT']
Set Up Grafana:

Install Grafana and add Prometheus as a data source.
Import or create dashboards to visualize Celery metrics.
10. Final Notes
Development Environment:
Use virtual environments to manage dependencies locally.

Error Handling & Logging:
Implement robust error handling and logging for production use.

Security:
Secure your Redis instance and protect your Teams webhook URL appropriately.
