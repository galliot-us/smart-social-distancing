FROM node:14-alpine
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json /frontend/
RUN npm install --production
COPY frontend /frontend
RUN npm run build
