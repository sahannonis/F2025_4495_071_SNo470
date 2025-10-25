const { loadRealData, getStops, getMalls } = require('./dist/src/dataLoader');

console.log('Testing API data loading...');

// Load the data
loadRealData();

// Test the data
const stops = getStops();
const malls = getMalls();

console.log('Stops loaded:', stops.length);
console.log('Malls loaded:', malls.length);

if (stops.length > 0) {
  console.log('First stop:', stops[0]);
}

if (malls.length > 0) {
  console.log('First mall:', malls[0]);
}

// Test filtering by distance (Vancouver downtown)
const centerLat = 49.2827;
const centerLng = -123.1207;
const radius = 1.5; // km

const nearbyStops = stops.filter(s => {
  const distance = kmBetween(centerLat, centerLng, s.stop_lat, s.stop_lon);
  return distance <= radius;
});

const nearbyMalls = malls.filter(m => {
  const distance = kmBetween(centerLat, centerLng, m.lat, m.lon);
  return distance <= radius;
});

console.log('Nearby stops (within 1.5km):', nearbyStops.length);
console.log('Nearby malls (within 1.5km):', nearbyMalls.length);

// Haversine distance function
function kmBetween(aLat, aLon, bLat, bLon) {
  const toRad = (d) => d * Math.PI / 180;
  const R = 6371;
  const dLat = toRad(bLat - aLat);
  const dLon = toRad(bLon - aLon);
  const s1 = Math.sin(dLat / 2);
  const s2 = Math.sin(dLon / 2);
  const aa = s1 * s1 + Math.cos(toRad(aLat)) * Math.cos(toRad(bLat)) * s2 * s2;
  return 2 * R * Math.asin(Math.sqrt(aa));
}
