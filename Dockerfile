# Use a MariaDB image as base
FROM mariadb:latest

# Set environment variables for MariaDB
ENV MARIADB_ROOT_PASSWORD=your_password
ENV MARIADB_DATABASE=plaivorb_db

# Copy schema and sample data
COPY db/schema.sql /docker-entrypoint-initdb.d/
COPY db/sample_data.sql /docker-entrypoint-initdb.d/
COPY db/functions_procedures.sql /docker-entrypoint-initdb.d/

# Expose MariaDB port
EXPOSE 3306

# You might want to build a separate app container for Python
# Or, build a single image for quick hackathon demo
# For the latter:
# RUN apt-get update && apt-get install -y python3 python3-pip
# COPY requirements.txt .
# RUN pip3 install -r requirements.txt
# COPY src/ /app/src/
# COPY notebooks/ /app/notebooks/
# COPY config.ini /app/
# WORKDIR /app
# CMD ["bash"] # Or specify a script to run
