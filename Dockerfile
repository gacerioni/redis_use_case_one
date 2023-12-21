FROM python:3.10.11

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Define the command to run your app using gunicorn as the WSGI server
CMD ["python", "./main.py"]