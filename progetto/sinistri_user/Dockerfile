FROM python:3.11-slim
WORKDIR /app
RUN pip install flask flask-cors mysql-connector-python pymongo dnspython cloudinary gradio_client
COPY . .
CMD ["python", "endpoint_5F_Sinistri_User.py"]