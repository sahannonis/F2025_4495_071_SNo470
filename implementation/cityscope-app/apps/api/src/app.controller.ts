import { Controller, Get, Param, Query } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

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
    const snap = await prisma.metricSnapshot.findFirst({
      where: { neighborhoodId: nId },
      orderBy: { capturedAt: 'desc' }
    });
    return snap ?? {};
  }

  @Get('compare')
  async compare(@Query('ids') ids?: string) {
    const arr = (ids ?? '').split(',').map(s => Number(s)).filter(Boolean);
    const snaps = await prisma.metricSnapshot.findMany({
      where: arr.length ? { neighborhoodId: { in: arr } } : {},
      orderBy: [{ neighborhoodId: 'asc' }, { capturedAt: 'desc' }]
    });
    const latest = new Map<number, any>();
    for (const s of snaps) if (!latest.has(s.neighborhoodId)) latest.set(s.neighborhoodId, s);
    return [...latest.values()];
  }
}
