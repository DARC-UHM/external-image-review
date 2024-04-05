# Set base image (host OS)
FROM python:alpine3.18

# Copy the everything to a new directory on the container
COPY . /external-image-review

# Set the working directory
WORKDIR /external-image-review

# Install dependencies
RUN pip install -r requirements.txt

# Listen on port 5000
EXPOSE 5000

# Set the directive to specify the executable that will run when the container is initiated
ENTRYPOINT ["gunicorn", "run:app", "-b", ":5000", "--threads", "4", "--workers", "4",  "--certfile", "cert/server.pem", "--keyfile", "cert/server.key"]
