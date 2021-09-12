#!/bin/bash

# This script shutsdown the instanace
# Note: shutting down will STOP in the instance, not TERMINATE

echo "Shutting system down..."

# Wait for a few seconds before shutting down in case clean up scripts are still running
# shutdown command cannot specify lengths under a minute so use sleep instead
sleep 10
shutsdown now
