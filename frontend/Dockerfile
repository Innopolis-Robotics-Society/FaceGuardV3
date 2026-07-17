FROM node:22-alpine

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

ARG VITE_CAMERA_SOURCE=browser
ARG VITE_API_BASE_URL=
ARG VITE_WS_BASE_URL=
ENV VITE_CAMERA_SOURCE=${VITE_CAMERA_SOURCE} \
    VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_WS_BASE_URL=${VITE_WS_BASE_URL}

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
