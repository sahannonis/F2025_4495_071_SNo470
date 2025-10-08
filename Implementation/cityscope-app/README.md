# CityScope Monorepo

## Run database
docker compose up -d

## Install deps
pnpm i

## Dev servers (two terminals)
pnpm --filter api run prisma db push
pnpm --filter api dev
pnpm --filter web dev

Docs: API Swagger at http://localhost:4000/docs
