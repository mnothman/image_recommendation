DOCKER_IMAGE_NAME := image_recommendation
DOCKER_CONTAINER_NAME := image_recommendation_container
DOCKER_PORT := 5000

# Default target
.PHONY: all
all: build run

# Build the Docker image
.PHONY: build
build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE_NAME) .

# Run the Docker container
.PHONY: run
run:
	@echo "Running Docker container..."
	docker run -d --name $(DOCKER_CONTAINER_NAME) -p $(DOCKER_PORT):5000 $(DOCKER_IMAGE_NAME)

# Stop the Docker container
.PHONY: stop
stop:
	@echo "Stopping Docker container..."
	docker stop $(DOCKER_CONTAINER_NAME)

# Remove the Docker container
.PHONY: remove
remove: stop
	@echo "Removing Docker container..."
	docker rm $(DOCKER_CONTAINER_NAME)

# Clean up Docker image and container
.PHONY: clean
clean: stop remove
	@echo "Removing Docker image..."
	docker rmi $(DOCKER_IMAGE_NAME)

# Show logs from the Docker container
.PHONY: logs
logs:
	@echo "Showing Docker container logs..."
	docker logs -f $(DOCKER_CONTAINER_NAME)
