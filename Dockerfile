FROM python:3.9
WORKDIR app
RUN pip install -r requirements.txt
CMD python app.py