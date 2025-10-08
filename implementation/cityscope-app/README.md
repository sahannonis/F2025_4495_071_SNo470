# CityScope Monorepo (MVP)

## Run database (Docker)
docker compose up -d

## Install dependencies
pnpm i

## Apply Prisma schema
pnpm --filter api run prisma db push

## Dev servers (two terminals)
pnpm --filter api dev   # API on http://localhost:4000 (Swagger at /docs)
pnpm --filter web dev   # Web on http://localhost:3000
