# Use an official Python runtime as a parent image
FROM python:3.11.3-slim-bullseye
ARG INSTALL_DEBUG
ENV PYTHONUNBUFFERED 1
ENV PATH=/root/.local/bin:$PATH

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies and cron
RUN apt-get update && \
    apt-get install -y --no-install-recommends libchromaprint-tools cron ffmpeg rsync && \
    rm -rf /var/lib/apt/lists/*


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip
#RUN pip install --user --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
RUN pip install --user -r requirements.txt

# Install cron
#RUN apt-get update && apt-get -y install cron

# Copy crontab file to the cron.d directory
COPY app-cron /etc/cron.d/app-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/app-cron

# Apply cron job
RUN crontab /etc/cron.d/app-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log

# Copy the entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]