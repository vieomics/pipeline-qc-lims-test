#!/bin/bash
echo ""
echo "============================================="
echo "          RIVER ANALYSIS TEMPLATE"
echo "============================================="
echo ""

# Default Environment Variables
echo ">> Default Environment Variables:"
echo "---------------------------------------------"
echo "UUID Job ID  : $job_id"
echo "CPU          : $cpu"
echo "Memory       : $memory"
echo "Time         : $time"
echo "RIVER_HOME   : $RIVER_HOME"
echo "---------------------------------------------"
echo ""

# Parameters
echo ">> Parameters:"
echo "---------------------------------------------"
echo "Repeat       : $repeat"
echo "File Path    : $file"
echo "Folder Path  : $dir"
echo "Integer      : $integer"
echo "Number(float): $number"
echo "String       : $string"
echo "Boolean      : $boolean"
echo "---------------------------------------------"
echo ""

# Bootstrap (for Custom Reverse Proxy)
echo ">> Bootstrap: Uncomment if you want to use custom reverse proxy"
echo "---------------------------------------------"
# Custom reverse location.
# Example: RStudio Server automatically redirects to `/` and restricts iframe usage.
echo "$job_id/" > "$RIVER_HOME/jobs/$job_id/job.proxy_location"

# Example: VS Code Server or JupyterLab requires reverse proxy.
echo "$job_id" > "$RIVER_HOME/jobs/$job_id/job.url"

# If the job is only exported via port (basic web app), still create this file but leave it empty.
touch "$RIVER_HOME/jobs/$job_id/job.url"
echo "---------------------------------------------"
echo ""

# Placeholder for Main Script Execution
echo "Put your main script here, using arguments from environment variables."

# Saying Hello World
for i in  $(seq 1 $repeat);
do
    echo Hello World $i
    sleep 1
done

echo ""
echo "✔ Analysis Completed!"
echo "============================================="
