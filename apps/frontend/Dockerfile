FROM node:20-alpine AS build

WORKDIR /workspace

COPY apps/frontend/package.json /workspace/apps/frontend/package.json
COPY packages/shared /workspace/packages/shared
COPY apps/frontend /workspace/apps/frontend

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /workspace/apps/frontend
RUN npm install
RUN npm run build

FROM nginx:1.27-alpine

ENV NGINX_API_UPSTREAM=http://api:8000
ENV NGINX_ENVSUBST_TEMPLATE_SUFFIX=.template
ENV NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx/conf.d

COPY apps/frontend/nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /workspace/apps/frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
