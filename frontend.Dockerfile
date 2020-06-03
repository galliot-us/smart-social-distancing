FROM node:14-alpine as builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json /frontend/
RUN npm install --production
COPY frontend /frontend
RUN npm run build

FROM scratch
COPY --from=builder /frontend/build /frontend/build
