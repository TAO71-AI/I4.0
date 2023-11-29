FROM python:3.9

RUN apt-get update && apt-get install -y git net-tools
WORKDIR /usr/src/I4

RUN git clone https://github.com/TAO71-AI/I4.0.git
WORKDIR /usr/src/I4/I4.0/LibI4/Python_AI

RUN pip install --upgrade -r requirements.txt
RUN pip install --upgrade -r requirements_recommended.txt

RUN chmod 777 ./
RUN chmod 777 ./*

CMD ["python", "ai_server_docker.py"]