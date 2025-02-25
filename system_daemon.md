Running as a System Service (Daemon)

sudo nano /etc/systemd/system/my_service.service

[Unit]
Description=My Python Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your_script.py
Restart=always
User=youruser
WorkingDirectory=/path/to/

[Install]
WantedBy=multi-user.target


Enable and start the service
sudo systemctl enable my_service
sudo systemctl start my_service


metaflow.service inside /etc/systemd/system/

[Unit]
Description=Run Metaflow Job
After=network.target

[Service]
ExecStart=/bin/bash -c "source /home/ubuntu/miniconda3/etc/profile.d/conda.sh && conda activate myenv && metaflow run MyFlow"
Restart=always
User=ubuntu
WorkingDirectory=/home/ubuntu
StandardOutput=append:/home/ubuntu/metaflow.log
StandardError=append:/home/ubuntu/metaflow.log
Environment="PATH=/home/ubuntu/miniconda3/envs/myenv/bin:/usr/bin:/bin"


metaflow.timer inside /etc/systemd/system/

[Unit]
Description=Schedule Metaflow Job

[Timer]
OnBootSec=5min
OnUnitActiveSec=10min
OnUnitInactiveSec=1s
Persistent=true

[Install]
WantedBy=timers.target

Managing systemd Services & Timers from VS Code

sudo systemctl daemon-reload
sudo systemctl enable metaflow.timer
sudo systemctl start metaflow.timer
sudo systemctl status metaflow.timer


Check if the timer is active
sudo systemctl list-timers --all
Check service status
sudo systemctl status my_metaflow

View logs
cat /home/youruser/my_flow.log

Force the job to run immediately for testing
sudo systemctl start my_metaflow.service


Go to Terminal > Configure Tasks (or manually create a tasks.json file inside .vscode/).

{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start Metaflow Timer",
            "type": "shell",
            "command": "sudo systemctl start metaflow.timer",
            "problemMatcher": [],
            "group": {
                "kind": "build",
                "isDefault": true
            }
        },
        {
            "label": "Stop Metaflow Timer",
            "type": "shell",
            "command": "sudo systemctl stop metaflow.timer",
            "problemMatcher": []
        },
        {
            "label": "Restart Metaflow Timer",
            "type": "shell",
            "command": "sudo systemctl restart metaflow.timer",
            "problemMatcher": []
        },
        {
            "label": "Check Metaflow Timer Status",
            "type": "shell",
            "command": "sudo systemctl status metaflow.timer",
            "problemMatcher": []
        },
        {
            "label": "Start Metaflow Service",
            "type": "shell",
            "command": "sudo systemctl start metaflow.service",
            "problemMatcher": []
        },
        {
            "label": "Stop Metaflow Service",
            "type": "shell",
            "command": "sudo systemctl stop metaflow.service",
            "problemMatcher": []
        },
        {
            "label": "Restart Metaflow Service",
            "type": "shell",
            "command": "sudo systemctl restart metaflow.service",
            "problemMatcher": []
        },
        {
            "label": "Check Metaflow Service Status",
            "type": "shell",
            "command": "sudo systemctl status metaflow.service",
            "problemMatcher": []
        },
        {
            "label": "Reload systemd Daemon",
            "type": "shell",
            "command": "sudo systemctl daemon-reload",
            "problemMatcher": []
        }
    ]
}

Step 3: (Optional) Assign Keyboard Shortcuts

[
    {
        "key": "ctrl+alt+s",
        "command": "workbench.action.tasks.runTask",
        "args": "Start Metaflow Timer"
    },
    {
        "key": "ctrl+alt+x",
        "command": "workbench.action.tasks.runTask",
        "args": "Stop Metaflow Timer"
    },
    {
        "key": "ctrl+alt+r",
        "command": "workbench.action.tasks.runTask",
        "args": "Restart Metaflow Timer"
    },
    {
        "key": "ctrl+alt+d",
        "command": "workbench.action.tasks.runTask",
        "args": "Check Metaflow Timer Status"
    }
]

git add .vscode/tasks.json
git

/usr/local/bin/my_daemon.sh

#!/bin/bash

exec 200>/var/lock/my_daemon.lock
flock -n 200 || exit 1  # Prevent concurrent execution

echo "Starting My Daemon at $(date)" >> /var/log/my_daemon.log

# Activate conda environment
source /home/ubuntu/miniconda3/bin/activate my_env

# Run Metaflow3 script
python /home/ubuntu/my_metaflow_script.py >> /var/log/my_daemon.log 2>&1

echo "Execution Completed at $(date)" >> /var/log/my_daemon.log
