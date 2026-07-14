FROM node:22.23.1-alpine3.23

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Vite embeds VITE_* variables at build time. Keep this argument after npm ci
# so switching camera mode does not invalidate the dependency layer.
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
