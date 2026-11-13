import type { FeatureCollection } from "geojson";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import network from "../data/osm-exploratory-network.json";

export function ExploratoryOsmMap() {
  return (
    <MapContainer center={[-12.0665, -75.2100]} zoom={15} scrollWheelZoom={false} className="osm-simulation-map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <GeoJSON
        data={network as FeatureCollection}
        style={(feature) => ({
          color: feature?.properties?.corridor ? "#34e6a2" : "#517c70",
          weight: feature?.properties?.corridor ? 4 : 1.5,
          opacity: feature?.properties?.corridor ? 0.95 : 0.65,
        })}
      />
    </MapContainer>
  );
}
