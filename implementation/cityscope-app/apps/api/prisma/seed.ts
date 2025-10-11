import { PrismaClient } from '@prisma/client';
import fs from 'fs';
import { parse } from 'csv-parse/sync';

const prisma = new PrismaClient();

type NeighborhoodRow = { id:string; name:string; city:string; centerLat:string; centerLng:string };
type ListingRow = { id:string; neighborhoodId:string; price:string; dateListed?:string };
type TransitRow = { id:string; neighborhoodId:string; type:string; lat:string; lng:string };
type MallRow = { id:string; neighborhoodId:string; name:string; lat:string; lng:string };

function readCSV<T>(path: string): T[] {
  const buf = fs.readFileSync(path);
  return parse(buf, { columns: true, skip_empty_lines: true, trim: true }) as T[];
}

function minMaxNormalize(value: number, min: number, max: number): number {
  if (max === min) return 50;
  return ((value - min) / (max - min)) * 100;
}

async function main() {
  const base = __dirname + '/../data/';
  const nRows = readCSV<NeighborhoodRow>(base + 'neighborhoods.csv');
  const lRows = readCSV<ListingRow>(base + 'listings.csv');
  const tRows = readCSV<TransitRow>(base + 'transit.csv');
  const mRows = readCSV<MallRow>(base + 'malls.csv');

  for (const n of nRows) {
    await prisma.neighborhood.upsert({
      where: { id: Number(n.id) },
      update: { name: n.name, city: n.city, centerLat: Number(n.centerLat), centerLng: Number(n.centerLng) },
      create: { id: Number(n.id), name: n.name, city: n.city, centerLat: Number(n.centerLat), centerLng: Number(n.centerLng) }
    });
  }

  const ids = nRows.map(n => Number(n.id));
  const avgRentMap = new Map<number, number>();
  const transitCountMap = new Map<number, number>();
  const mallCountMap = new Map<number, number>();

  for (const id of ids) {
    const listings = lRows.filter(l => Number(l.neighborhoodId) === id);
    const avg = listings.length ? listings.reduce((s, r) => s + Number(r.price), 0) / listings.length : 0;
    avgRentMap.set(id, Math.round(avg));

    const tCount = tRows.filter(t => Number(t.neighborhoodId) === id).length;
    transitCountMap.set(id, tCount);

    const mCount = mRows.filter(m => Number(m.neighborhoodId) === id).length;
    mallCountMap.set(id, mCount);
  }

  const rents = [...avgRentMap.values()];
  const transits = [...transitCountMap.values()];
  const malls = [...mallCountMap.values()];

  const rentMin = Math.min(...rents), rentMax = Math.max(...rents);
  const transitMin = Math.min(...transits), transitMax = Math.max(...transits);
  const mallMin = Math.min(...malls), mallMax = Math.max(...malls);

  for (const id of ids) {
    const avgRent = avgRentMap.get(id) ?? 0;
    const transitCount = transitCountMap.get(id) ?? 0;
    const mallCount = mallCountMap.get(id) ?? 0;

    const rentNorm = minMaxNormalize(avgRent, rentMin, rentMax);
    const affordability = 100 - rentNorm; // cheaper is better
    const transitNorm = minMaxNormalize(transitCount, transitMin, transitMax);
    const amenityNorm = minMaxNormalize(mallCount, mallMin, mallMax);

    const score = Math.round(0.55 * affordability + 0.35 * transitNorm + 0.10 * amenityNorm);

    await prisma.metricSnapshot.create({
      data: { neighborhoodId: id, avgRent, transitCount, mallCount, score }
    });
  }

  console.log('Seed completed.');
}

main().catch(e => { console.error(e); process.exit(1); }).finally(async () => prisma.$disconnect());
