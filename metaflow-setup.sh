# /var/lib/cloud/scripts/per-boot/metaflow-setup.sh

#!/bin/bash

# Log everything
exec > /var/log/metaflow-userdata.log 2>&1
echo "Starting Metaflow user-data setup..."

# Define variables
USER="ubuntu"  # Change to your actual user
METAFLOW_SCRIPT="/home/$USER/my_flow.py"
CONDA_ENV="myenv"
CONDA_PATH="/home/$USER/miniconda3"
METAFLOW_SERVICE="/etc/systemd/system/metaflow.service"
METAFLOW_TIMER="/etc/systemd/system/metaflow.timer"

# Install dependencies
echo "Updating and installing dependencies..."
apt update -y && apt install -y python3-pip sudo curl

# Install Miniconda if not installed
if [ ! -d "$CONDA_PATH" ]; then
    echo "Installing Miniconda..."
    curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p "$CONDA_PATH"
    rm /tmp/miniconda.sh
fi

# Load Conda and create environment if not exists
echo "Setting up Conda environment..."
source "$CONDA_PATH/etc/profile.d/conda.sh"
conda create -y -n $CONDA_ENV python=3.9
conda activate $CONDA_ENV
pip install metaflow  # Ensure Metaflow is installed

# Create a simple Metaflow script if not exists
if [ ! -f "$METAFLOW_SCRIPT" ]; then
    echo "Creating a sample Metaflow script..."
    cat <<EOF > "$METAFLOW_SCRIPT"
from metaflow import FlowSpec, step
import logging

logging.basicConfig(filename='/home/$USER/metaflow.log', level=logging.INFO)

class MyFlow(FlowSpec):

    @step
    def start(self):
        logging.info("Starting Metaflow job...")
        self.next(self.run_task)

    @step
    def run_task(self):
        logging.info("Running long task...")
        self.next(self.end)

    @step
    def end(self):
        logging.info("Job completed!")

if __name__ == '__main__':
    MyFlow()
EOF
    chown $USER:$USER "$METAFLOW_SCRIPT"
fi

# Create systemd service
echo "Creating systemd service..."
cat <<EOF > "$METAFLOW_SERVICE"
[Unit]
Description=Run Metaflow Job
After=network.target

[Service]
ExecStart=/bin/bash -c "source $CONDA_PATH/etc/profile.d/conda.sh && conda activate $CONDA_ENV && metaflow run MyFlow"
Restart=always
User=$USER
WorkingDirectory=/home/$USER
StandardOutput=append:/home/$USER/metaflow.log
StandardError=append:/home/$USER/metaflow.log
Environment="PATH=$CONDA_PATH/envs/$CONDA_ENV/bin:/usr/bin:/bin"
EOF

# Create systemd timer
echo "Creating systemd timer..."
cat <<EOF > "$METAFLOW_TIMER"
[Unit]
Description=Schedule Metaflow Job

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Set correct permissions
chmod 644 "$METAFLOW_SERVICE" "$METAFLOW_TIMER"

# Reload systemd and start services
echo "Reloading systemd..."
systemctl daemon-reload
systemctl enable metaflow.timer
systemctl start metaflow.timer

echo "Metaflow setup complete!"
