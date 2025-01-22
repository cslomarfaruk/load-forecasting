FROM python:3.9-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_ENV production
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 3000
# CMD ["python", "main.py"]
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "main:app"]
ENV FLASK_APP=main.py 
