import fs from 'fs';
import { parse } from 'csv-parse/sync';

export type Stop = { stop_id: string; stop_name: string; stop_lat: number; stop_lon: number };
export type Mall = { name: string; lat: number; lon: number };

// Load once at startup
let STOPS: Stop[] = [];
let MALLS: Mall[] = [];

export function loadRealData() {
  try {
    const stopsPath = __dirname + '/../../data/real/stops.txt';
    console.log('Loading stops from:', stopsPath);
    if (fs.existsSync(stopsPath)) {
      const raw = fs.readFileSync(stopsPath);
      const rows = parse(raw, { columns: true, skip_empty_lines: true, trim: true, delimiter: ',' });
      console.log('Parsed stops rows:', rows.length);
      STOPS = rows.map((r: any) => ({
        stop_id: String(r.stop_id),
        stop_name: String(r.stop_name ?? ''),
        stop_lat: Number(r.stop_lat),
        stop_lon: Number(r.stop_lon),
      })).filter((s: Stop) => Number.isFinite(s.stop_lat) && Number.isFinite(s.stop_lon));
      console.log('Loaded stops:', STOPS.length);
    } else {
      console.log('Stops file not found at:', stopsPath);
    }
  } catch (e) {
    console.error('Failed loading stops.txt', e);
  }

  try {
    const mallsPath = __dirname + '/../../data/real/malls.csv';
    console.log('Loading malls from:', mallsPath);
    if (fs.existsSync(mallsPath)) {
      const raw = fs.readFileSync(mallsPath);
      const rows = parse(raw, { columns: true, skip_empty_lines: true, trim: true, delimiter: ',' });
      console.log('Parsed malls rows:', rows.length);
      MALLS = rows.map((r: any) => ({
        name: String(r.name ?? 'Mall'),
        lat: Number(r.lat ?? r['@lat'] ?? r['lat:lat']),
        lon: Number(r.lon ?? r['@lon'] ?? r['lon:lon']),
      })).filter((m: Mall) => Number.isFinite(m.lat) && Number.isFinite(m.lon));
      console.log('Loaded malls:', MALLS.length);
    } else {
      console.log('Malls file not found at:', mallsPath);
    }
  } catch (e) {
    console.error('Failed loading malls.csv', e);
  }
}

export function getStops() { return STOPS; }
export function getMalls() { return MALLS; }

// Haversine distance in km
export function kmBetween(aLat:number,aLon:number,bLat:number,bLon:number) {
  const toRad = (d:number)=>d*Math.PI/180;
  const R=6371, dLat=toRad(bLat-aLat), dLon=toRad(bLon-aLon);
  const s1=Math.sin(dLat/2), s2=Math.sin(dLon/2);
  const aa = s1*s1 + Math.cos(toRad(aLat))*Math.cos(toRad(bLat))*s2*s2;
  return 2*R*Math.asin(Math.sqrt(aa));
}
