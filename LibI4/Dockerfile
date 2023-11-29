FROM python:3.9

RUN apt-get update && apt-get install -y git
WORKDIR /usr/src/I4

RUN git clone https://github.com/TAO71-AI/I4.0.git

COPY /usr/src/I4/I4.0/LibI4/Python_AI/* /usr/src/I4/
RUN rm -r I4.0

RUN pip install --upgrade -r requirements.txt
RUN pip install --upgrade -r requirements_recommended.txt

CMD ["python", "ai_server_docker.py"]