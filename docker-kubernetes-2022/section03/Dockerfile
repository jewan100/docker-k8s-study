FROM node 

WORKDIR /app

COPY package.json /app

RUN npm install

COPY . /app

ARG DEFAULT_PORT=80
# 환경 변수 설정

ENV PORT $DEFAULT_PORT
# 환경 변수

EXPOSE $PORT
# `$`로 환경 변수 참조

CMD ["node", "server.js"]