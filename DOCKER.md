# Docker Environment Configuration
This Docker container has been configured primarily for development purposes, preserving the full functionality of the project, including environment virtualization with Poetry running inside the container. This setup is not recommended for production environments as containerization itself ensures dependency isolation, and additional virtualization within the container can lead to unnecessary overhead.

## System Requirements
To run the application within a container, Docker and docker-compose must be installed:
[Docker 🐳](https://docs.docker.com/desktop/)
[Docker Compose 🐳](https://docs.docker.com/compose/install/)

## Repository Download
Clone the repository into a new, empty folder:
```
mkdir [folderName]
cd [folderName]
git clone https://github.com/pymasterspl/reddit.git .
```
Note: The period at the end of the git clone command clones the repository into the current folder. It is important that the folder is empty!!!


## Option 1: Automatic Migration Execution
### Executing the following commands will build the image, create the container, and perform automatic database migrations. You can monitor the application status through the logs.
```bash
docker-compose up -d
docker-compose logs -f
Ctrl + C  # To stop monitoring the logs
```

### Creating a Superuser
```bash
docker-compose exec web bash
poetry run python manage.py createsuperuser
Ctrl + D  # To exit the container
```

### Monitoring Logs
```bash
docker-compose logs -f
```

## Option 2: Isolated Container Mode
### Running the container in isolated mode and entering the `poetry` shell to perform migrations and create a superuser.
```bash
cp env-template .env
docker-compose build
docker-compose run web bash
poetry install
poetry shell
python manage.py migrate
python manage.py createsuperuser
Ctrl + D  # To exit the poetry shell
Ctrl + D  # To exit the container
docker-compose down
docker-compose up -d
docker-compose logs -f
```

## Option 3: Running the Container with Migration and Superuser Creation
```bash
cp env-template .env
docker-compose build
docker-compose run web bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
Ctrl + D  # To exit the container
docker-compose down
docker-compose up -d
docker-compose logs -f
```



