FROM python:3.11-slim
WORKDIR /app
RUN pip install flask flask-cors mysql-connector-python pymongo dnspython
COPY . .
CMD ["python", "endpoint_5F_log_reg.py"]