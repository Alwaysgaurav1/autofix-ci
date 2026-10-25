FROM oven/bun:1.1 as builder

WORKDIR /app

COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile || bun install

COPY . .
RUN bun run build

EXPOSE 3000

CMD ["bun", "run", "start"]
