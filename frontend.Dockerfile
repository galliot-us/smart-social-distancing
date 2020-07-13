FROM node:14-alpine as builder
WORKDIR /frontend
COPY frontend/package.json frontend/yarn.lock /frontend/
RUN yarn install --production
COPY frontend /frontend
RUN yarn build

FROM scratch
COPY --from=builder /build /build
