# Install the base requirements for the app.
FROM python:3.8
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Launch of the script:
CMD python ./main.py --config_path ./config/config.json --jira_credentials ./config/jira_credentials.json --google_credentials_path ./config/google_credentials.json --debug
# you can use use "docker-compose logs" for checking script output - or use "> ./monitor.log"

# Alternatively you can comment out the previous line and setup just a simple process to keep container up & running if you want to get inside it with
# "docker-compose exec agile-monitor bash"
# CMD tail -f /dev/null
# Do not forget to run "docker-compose build" after that to refresh the image