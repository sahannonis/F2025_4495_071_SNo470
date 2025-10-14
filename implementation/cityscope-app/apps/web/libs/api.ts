export async function fetchNeighborhoods() {
    const res = await fetch("http://localhost:3000/neighborhoods");
    return res.json();
  }
  