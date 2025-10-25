import { Controller, Get, Param, Query } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { getMalls, getStops, kmBetween, loadRealData } from './dataLoader';
const prisma = new PrismaClient();

loadRealData(); // load GTFS + OSM once

@Controller()
export class AppController {
  @Get('neighborhoods')
  async neighborhoods() {
    return prisma.neighborhood.findMany({
      include: { snapshots: { orderBy: { capturedAt: 'desc' }, take: 1 } }
    });
  }

  @Get('neighborhoods/:id/summary')
  async summary(@Param('id') id: string) {
    const nId = Number(id);
    const neighborhood = await prisma.neighborhood.findUnique({ where: { id: nId } });
    if (!neighborhood) return {};

    // Calculate real transit and mall counts
    const radius = 1.5; // km
    const stops = getStops().filter(s =>
      kmBetween(neighborhood.centerLat, neighborhood.centerLng, s.stop_lat, s.stop_lon) <= radius
    );
    const malls = getMalls().filter(m =>
      kmBetween(neighborhood.centerLat, neighborhood.centerLng, m.lat, m.lon) <= radius
    );

    // Get existing snapshot or create new one
    const snap = await prisma.metricSnapshot.findFirst({
      where: { neighborhoodId: nId },
      orderBy: { capturedAt: 'desc' }
    });

    return {
      ...snap,
      transitCount: stops.length,
      mallCount: malls.length,
      // Keep existing avgRent and score if they exist
      avgRent: snap?.avgRent ?? 0,
      score: snap?.score ?? 0
    };
  }

  @Get('compare')
  async compare(@Query('ids') ids?: string) {
    const arr = (ids ?? '').split(',').map(s => Number(s)).filter(Boolean);
    if (!arr.length) return [];

    const results = [];
    for (const neighborhoodId of arr) {
      const neighborhood = await prisma.neighborhood.findUnique({ where: { id: neighborhoodId } });
      if (!neighborhood) continue;

      // Calculate real transit and mall counts
      const radius = 1.5; // km
      const stops = getStops().filter(s =>
        kmBetween(neighborhood.centerLat, neighborhood.centerLng, s.stop_lat, s.stop_lon) <= radius
      );
      const malls = getMalls().filter(m =>
        kmBetween(neighborhood.centerLat, neighborhood.centerLng, m.lat, m.lon) <= radius
      );

      // Get existing snapshot for other data
      const snap = await prisma.metricSnapshot.findFirst({
        where: { neighborhoodId },
        orderBy: { capturedAt: 'desc' }
      });

      results.push({
        neighborhoodId,
        transitCount: stops.length,
        mallCount: malls.length,
        avgRent: snap?.avgRent ?? 0,
        score: snap?.score ?? 0
      });
    }
    return results;
  }

  // NEW: Overlay endpoints
  @Get('overlay/stops')
  async stops(@Query('neighborhoodId') neighborhoodId?: string, @Query('radiusKm') radiusKm: string = '1.5') {
    console.log('API: overlay/stops called with', { neighborhoodId, radiusKm });
    const id = Number(neighborhoodId);
    if (!id) {
      console.log('API: No neighborhood ID provided');
      return [];
    }
    const n = await prisma.neighborhood.findUnique({ where: { id } });
    if (!n) {
      console.log('API: Neighborhood not found for ID', id);
      return [];
    }
    const radius = Number(radiusKm) || 1.5;
    const allStops = getStops();
    console.log('API: Total stops loaded:', allStops.length);
    const stops = allStops.filter(s =>
      kmBetween(n.centerLat, n.centerLng, s.stop_lat, s.stop_lon) <= radius
    );
    console.log('API: Filtered stops within radius:', stops.length);
    return stops.slice(0, 1000); // safety cap
  }

  @Get('overlay/malls')
  async malls(@Query('neighborhoodId') neighborhoodId?: string, @Query('radiusKm') radiusKm: string = '3') {
    console.log('API: overlay/malls called with', { neighborhoodId, radiusKm });
    const id = Number(neighborhoodId);
    if (!id) {
      console.log('API: No neighborhood ID provided');
      return [];
    }
    const n = await prisma.neighborhood.findUnique({ where: { id } });
    if (!n) {
      console.log('API: Neighborhood not found for ID', id);
      return [];
    }
    const radius = Number(radiusKm) || 3;
    const allMalls = getMalls();
    console.log('API: Total malls loaded:', allMalls.length);
    const malls = allMalls.filter(m =>
      kmBetween(n.centerLat, n.centerLng, m.lat, m.lon) <= radius
    );
    console.log('API: Filtered malls within radius:', malls.length);
    return malls.slice(0, 1000);
  }
}
