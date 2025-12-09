FROM node 

WORKDIR /app

COPY package.json /app
# 의존성 파일만 먼저 복사
# 의존성 설치가 자주 변경되지 않는다면 이후 레이어 캐싱으로 빌드 속도 향상

RUN npm install
# 캐싱된 레이어를 활용하여 의존성 설치

COPY . /app

EXPOSE 80

CMD ["node", "server.js"]