FROM node:14-alpine as builder
WORKDIR /frontend
COPY frontend/package.json frontend/yarn.lock /frontend/
RUN yarn install --network-timeout 1000000 --production
COPY frontend /frontend
RUN yarn build

FROM scratch
COPY --from=builder /frontend/build /frontend/build
