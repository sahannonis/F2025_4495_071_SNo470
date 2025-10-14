export type Snapshot = {
    id: number;
    neighborhoodId: number;
    avgRent: number;
    transitCount: number;
    mallCount: number;
    score: number;
    capturedAt: string;
  };
  
  export type Neighborhood = {
    id: number;
    name: string;
    city: string;
    centerLat: number;
    centerLng: number;
    snapshots?: Snapshot[];
  };
  
  export type Summary = Snapshot;
  