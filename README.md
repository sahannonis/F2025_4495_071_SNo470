F2025_4495_071_SNo470
📍 CityScope: Real Estate & Community Data Explorer

Student: Sahan Nonis (ID: 300389470)
Email: pattinikuttiges@student.douglascollege.ca
Instructor: Bambang Sarif

🌐 Project Overview
CityScope is a real estate and community data explorer that helps users evaluate and compare neighborhoods based on affordability, transit access, and amenities.
The application combines multiple datasets into a unified livability score to provide clear insights into community conditions and real estate trends.

🎯 Objectives
Integrate housing, transit, and amenity datasets into a single platform.
Automate data loading via an ETL pipeline (Extract, Transform, Load).
Provide REST API endpoints for frontend consumption.
Develop a livability scoring model (affordability, transit, amenities).
Enable comparison of multiple neighborhoods.

⚙️ Tech Stack
Backend: NestJS
 + TypeScript

Database: Prisma ORM with SQLite (Phase 1 MVP)
ETL: Custom seeding script (prisma/seed.ts)
API: REST endpoints for neighborhood data and comparisons
Containerization: Docker & Docker Compose (future PostgreSQL setup)

📂 Repository Structure
cityscope-app/
├── apps/
│   └── api/                 # NestJS backend
│       ├── prisma/          # Prisma schema + seed script
│       ├── src/             # API source code
│       └── package.json
├── data/                    # Mock datasets (CSV)
├── documents/               # Proposal + progress reports
└── README.md                # Project overview (this file)

🚀 Current Features (Phase 1 Complete)
Database schema: Neighborhood + MetricSnapshot
ETL pipeline: CSV → metrics → DB
Livability score formula:
55% affordability
35% transit access
10% amenities

API Endpoints:
GET /neighborhoods → list neighborhoods
GET /neighborhoods/:id/summary → summary by neighborhood
GET /compare?ids=1,2,3 → compare neighborhoods


📖 How to Run (Backend MVP)
# Clone repo
git clone <repo-url>
cd cityscope-app

# Install dependencies
pnpm install

# Generate Prisma client + push schema
pnpm --filter api exec prisma generate
pnpm --filter api exec prisma db push

# Seed database
pnpm --filter api run seed

# Run backend
pnpm --filter api run start:dev
