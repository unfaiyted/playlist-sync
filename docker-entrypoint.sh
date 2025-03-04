#!/bin/sh

# Replace the cron schedule with the one from .env
#sed -i "s|* * * * *|$CRON_SCHEDULE|g" /etc/cron.d/app-cron

# Apply the updated cron job
#crontab /etc/cron.d/app-cron

# Start cron in the foreground
cron -f