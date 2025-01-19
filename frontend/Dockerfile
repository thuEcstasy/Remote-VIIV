FROM node:18 AS builder

WORKDIR /build

COPY package.json yarn.lock ./

RUN yarn config set registry https://registry.npmmirror.com && yarn

COPY . .

RUN yarn build

FROM node:18 AS runner

WORKDIR /app

COPY --from=builder /build/.next/standalone .

COPY --from=builder /build/.next/static .next/static

COPY --from=builder /build/public public

ENV PORT 80

EXPOSE 80

CMD ["node", "server.js"]