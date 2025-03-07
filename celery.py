import psutil
import logging
from celery import Celery
from celery.utils.log import get_task_logger
from metaflow import FlowSpec, step
import redis

# Set up Celery app with Redis as the broker
app = Celery('tasks', broker='redis://localhost:6379/0')

# Configure logging
logger = get_task_logger(__name__)

# Redis client for queue length monitoring
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# Function to get CPU load
def get_cpu_load():
    return psutil.cpu_percent(interval=1)

# Function to get the current queue length
def get_queue_length():
    return redis_client.llen("celery")

# Function to get number of CPU cores and set initial worker count
def get_initial_worker_count():
    cpu_cores = psutil.cpu_count(logical=False)  # Get the number of physical CPU cores
    # Set initial number of workers based on CPU cores
    initial_workers = cpu_cores * 2  # For example, start with 2 workers per CPU core
    return initial_workers

# Function to scale workers based on CPU load and queue length
def scale_workers():
    cpu_load = get_cpu_load()
    queue_length = get_queue_length()

    # Fine-tuned worker scaling logic based on CPU load and queue length
    if cpu_load > 85 or queue_length > 100:  # High CPU load or long queue length
        max_workers = 15  # Increase the max workers if CPU load and queue length are high
        min_workers = 7  # Keep a decent minimum number of workers
    elif cpu_load < 50 and queue_length < 30:  # Low CPU load and short queue
        max_workers = 10  # Reduce worker count
        min_workers = 4  # Keep workers idle if possible
    else:
        # Default scaling logic
        max_workers = 12
        min_workers = 6

    logger.info(f"Scaling workers - CPU Load: {cpu_load}%, Queue Length: {queue_length}")
    return min_workers, max_workers

# Get initial worker count based on CPU cores
initial_worker_count = get_initial_worker_count()

# Celery configuration to dynamically set autoscale based on CPU and queue length
min_workers, max_workers = scale_workers()

app.conf.update(
    worker_autoscale=(max_workers, min_workers),  # Define autoscale behavior
    worker_concurrency=initial_worker_count,  # Set initial number of workers
)

# Metaflow workflow
class MyFlow(FlowSpec):

    @step
    def start(self):
        logger.info("Starting Metaflow task")
        self.next(self.process)

    @step
    def process(self):
        logger.info("Processing inside Metaflow workflow")
        self.next(self.end)

    @step
    def end(self):
        logger.info("Metaflow task completed")

# Celery task that runs the Metaflow workflow
@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def run_metaflow(self):
    try:
        logger.info("Triggering Metaflow workflow...")
        # Trigger the Metaflow workflow
        MyFlow()
        return "Metaflow workflow executed successfully"
    except Exception as e:
        logger.error(f"Error in Metaflow execution: {e}")
        raise self.retry(exc=e)



# Load test

from celery_worker import run_metaflow

# Trigger 200 tasks to simulate more load
for _ in range(200):
    run_metaflow.apply_async()
    print("Task triggered")

3️⃣ Monitoring Performance with Flower
As you run the load test, keep Flower running on http://localhost:5555 to monitor:

Worker Scaling: You should now see the worker count increasing and decreasing based on the load conditions we set.
Task Queue Length: Observe how the queue length grows and how quickly tasks get processed.
CPU and Memory Usage: Flower will show the CPU usage of each worker and give you insights into whether the workers are under heavy load or idle.


Advanced Monitoring with Metrics
If you want more advanced monitoring, such as task latency, success rate, and more detailed metrics, you can integrate Prometheus and Grafana with Celery. Here’s a high-level overview of setting this up:

Install Prometheus and Grafana for Monitoring:
Install Prometheus and Grafana (via Docker for simplicity):

bash
Copy
Edit
docker run -d -p 9090:9090 prom/prometheus
docker run -d -p 3000:3000 grafana/grafana
Install Celery Prometheus Exporter:

bash
Copy
Edit
pip install celery-prometheus
Enable Prometheus Exporter in Celery: Add the following to your celery_worker.py file to enable Prometheus metrics:

python
Copy
Edit
from celery_prometheus import CeleryPrometheus

CeleryPrometheus(app)
Configure Prometheus to scrape metrics from Celery:

In Prometheus configuration (prometheus.yml), add the Celery exporter endpoint:
yaml
Copy
Edit
scrape_configs:
  - job_name: 'celery'
    static_configs:
      - targets: ['localhost:5555']  # Prometheus will scrape metrics from Celery Flower
Configure Grafana:

Connect Grafana to Prometheus and set up dashboards to monitor Celery workers' CPU usage, task queue length, task completion time, etc.
5️⃣ Evaluate and Adjust the Configuration
After running the load test and monitoring the performance:

Task Completion Time: If tasks are taking too long to complete, consider increasing worker concurrency or splitting tasks into smaller, parallelizable sub-tasks.
CPU and Memory Usage: If you see that CPU usage is consistently high, you may need to adjust the scaling thresholds or worker concurrency.
Queue Length: If the queue length remains high even after scaling up, you might need to increase the scaling limit (max workers) or optimize the tasks to process faster.
