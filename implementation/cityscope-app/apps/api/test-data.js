const fs = require('fs');
const { parse } = require('csv-parse/sync');

console.log('Testing data loading...');

// Test stops loading
try {
  const stopsPath = __dirname + '/data/real/stops.txt';
  console.log('Stops path:', stopsPath);
  console.log('File exists:', fs.existsSync(stopsPath));
  
  if (fs.existsSync(stopsPath)) {
    const raw = fs.readFileSync(stopsPath);
    console.log('File size:', raw.length);
    const rows = parse(raw, { columns: true, skip_empty_lines: true, trim: true, delimiter: ',' });
    console.log('Parsed rows:', rows.length);
    console.log('First row:', rows[0]);
    
    const stops = rows.map((r) => ({
      stop_id: String(r.stop_id),
      stop_name: String(r.stop_name ?? ''),
      stop_lat: Number(r.stop_lat),
      stop_lon: Number(r.stop_lon),
    })).filter((s) => Number.isFinite(s.stop_lat) && Number.isFinite(s.stop_lon));
    
    console.log('Valid stops:', stops.length);
    console.log('First stop:', stops[0]);
  }
} catch (e) {
  console.error('Error loading stops:', e);
}

// Test malls loading
try {
  const mallsPath = __dirname + '/data/real/malls.csv';
  console.log('Malls path:', mallsPath);
  console.log('File exists:', fs.existsSync(mallsPath));
  
  if (fs.existsSync(mallsPath)) {
    const raw = fs.readFileSync(mallsPath);
    console.log('File size:', raw.length);
    const rows = parse(raw, { columns: true, skip_empty_lines: true, trim: true, delimiter: ',' });
    console.log('Parsed rows:', rows.length);
    console.log('First row:', rows[0]);
    
    const malls = rows.map((r) => ({
      name: String(r.name ?? 'Mall'),
      lat: Number(r.lat ?? r['@lat'] ?? r['lat:lat']),
      lon: Number(r.lon ?? r['@lon'] ?? r['lon:lon']),
    })).filter((m) => Number.isFinite(m.lat) && Number.isFinite(m.lon));
    
    console.log('Valid malls:', malls.length);
    console.log('First mall:', malls[0]);
  }
} catch (e) {
  console.error('Error loading malls:', e);
}
