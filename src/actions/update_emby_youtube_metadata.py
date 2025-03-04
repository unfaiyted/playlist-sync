import paramiko
from getpass import getpass
from src.utils.logger import get_action_logger
import os

logger = get_action_logger("update_emby_youtube_metadata")

def run_command_in_container(host, username, key_filename, key_password, container_name, command):
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the remote server using the key
        ssh.connect(
            hostname=host,
            username=username,
            key_filename=key_filename,
            passphrase=key_password
        )

        # Construct the docker exec command
        docker_command = f"docker exec {container_name} {command}"

        # Execute the command
        stdin, stdout, stderr = ssh.exec_command(docker_command)

        # Get the output
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        if error:
            logger.error(f"Error executing command in container '{container_name}': {error}")
        else:
            logger.info(f"Command executed successfully in container '{container_name}'")
            logger.info(f"Output: {output}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    finally:
        if 'ssh' in locals():
            ssh.close()


# Usage
host = "192.168.0.101"
username = "faiyt"  # Your SSH username
key_filename = os.path.expanduser("~/.ssh/id_ed25519")  # Use os.path for cross-platform compatibility
container_name = "tubearchivist-emby"
command = "python main.py"

# Prompt for the key passphrase securely
key_password = "dragon"

print(f"Running '{command}' in container '{container_name}' on host {host}")
run_command_in_container(host, username, key_filename, key_password, container_name, command)