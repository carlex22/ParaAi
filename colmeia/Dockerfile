FROM python:3.11-slim

RUN apt-get update && apt-get install -y git

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

RUN chmod +x entrypoint.sh
EXPOSE 7860

CMD ["./entrypoint.sh"]

