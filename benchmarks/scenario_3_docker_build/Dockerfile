FROM python:3.12-slim
WORKDIR /app
# BUG: apt-get install fails without apt-get update
RUN apt-get install -y --no-install-recommends curl
COPY . .
CMD ["python", "-m", "http.server", "8080"]
