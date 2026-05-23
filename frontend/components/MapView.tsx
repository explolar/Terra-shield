"use client";

import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Rectangle,
  CircleMarker,
  Tooltip as LeafletTooltip,
  useMap,
  useMapEvents,
} from "react-leaflet";
import type {
  Layer as LeafletLayer,
  PathOptions,
  LatLngBoundsExpression,
} from "leaflet";
import type { Feature, FeatureCollection } from "geojson";
import type {
  LayerResponse,
  PointFeatureCollection,
  LineFeatureCollection,
} from "@/lib/types";
import {
  productValueConfig,
  valueToColor,
} from "@/lib/colors";
import {
  DARK_BASEMAP,
  bboxToLeafletBounds,
} from "@/lib/presets";

interface MapViewProps {
  bbox: [number, number, number, number];
  layer: LayerResponse | null;
  drawMode: boolean;
  onDrawComplete: (bbox: [number, number, number, number]) => void;
  // ResilienceOR overlays
  shelters?: PointFeatureCollection | null;
  route?: LineFeatureCollection | null;
  // optional: click a state polygon to select it as AOI
  onSelectState?: (name: string, bbox: [number, number, number, number]) => void;
}

// Imperatively fly the map when the AOI changes.
function FlyToBounds({
  bounds,
}: {
  bounds: LatLngBoundsExpression;
}) {
  const map = useMap();
  useEffect(() => {
    map.flyToBounds(bounds, { padding: [40, 40], duration: 1.1 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(bounds)]);
  return null;
}

// Two-click bbox drawing.
function DrawHandler({
  active,
  onComplete,
}: {
  active: boolean;
  onComplete: (bbox: [number, number, number, number]) => void;
}) {
  const cornersRef = useMemo(() => ({ first: null as [number, number] | null }), []);
  useMapEvents({
    click(e) {
      if (!active) return;
      const pt: [number, number] = [e.latlng.lng, e.latlng.lat]; // [lon, lat]
      if (!cornersRef.first) {
        cornersRef.first = pt;
      } else {
        const [lon1, lat1] = cornersRef.first;
        const [lon2, lat2] = pt;
        cornersRef.first = null;
        onComplete([
          Math.min(lon1, lon2),
          Math.min(lat1, lat2),
          Math.max(lon1, lon2),
          Math.max(lat1, lat2),
        ]);
      }
    },
  });
  return null;
}

function ResizeFix() {
  const map = useMap();
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 200);
    return () => clearTimeout(t);
  }, [map]);
  return null;
}

// ---- India boundary base layers (static, behind analysis) ----

function useStaticGeo(
  url: string,
  enabled: boolean = true,
): FeatureCollection | null {
  const [data, setData] = useState<FeatureCollection | null>(null);
  useEffect(() => {
    if (!enabled || data) return;
    let alive = true;
    fetch(url)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => alive && d && setData(d))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [url, enabled, data]);
  return data;
}

const OUTLINE_STYLE: PathOptions = {
  color: "#34d399",
  weight: 1.4,
  opacity: 0.55,
  fill: false,
  // soft glow effect
  className: "india-outline-glow",
};

const STATES_STYLE: PathOptions = {
  color: "#22d3ee",
  weight: 0.5,
  opacity: 0.16,
  fill: false,
  interactive: false,
};

const DISTRICTS_STYLE: PathOptions = {
  color: "#64748b",
  weight: 0.4,
  opacity: 0.14,
  fill: false,
  interactive: false,
};

// Track zoom for conditional district rendering.
function ZoomWatcher({ onZoom }: { onZoom: (z: number) => void }) {
  const map = useMap();
  useEffect(() => {
    onZoom(map.getZoom());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useMapEvents({
    zoomend() {
      onZoom(map.getZoom());
    },
  });
  return null;
}

function IndiaBoundaries({
  zoom,
  onSelectState,
}: {
  zoom: number;
  onSelectState?: (name: string, bbox: [number, number, number, number]) => void;
}) {
  const outline = useStaticGeo("/geo/india_outline.geojson");
  const states = useStaticGeo("/geo/india_states.geojson");
  // Districts are large (~340 KB); only fetch once the user zooms in.
  const districts = useStaticGeo("/geo/india_districts.geojson", zoom >= 7);

  // States become clickable AOI-selectors only when a handler is provided.
  const interactiveStates = !!onSelectState;

  function onEachState(feature: Feature, leafletLayer: LeafletLayer) {
    if (!onSelectState) return;
    const name = (feature.properties as any)?.STATE as string | undefined;
    if (!name) return;
    leafletLayer.bindTooltip(
      `<div style="font-size:11px"><b>${name}</b><br/>click to set as AOI</div>`,
      { sticky: true, opacity: 0.95 },
    );
    leafletLayer.on({
      click() {
        const b = (leafletLayer as any).getBounds?.();
        if (!b) return;
        onSelectState(name, [
          b.getWest(),
          b.getSouth(),
          b.getEast(),
          b.getNorth(),
        ]);
      },
      mouseover() {
        (leafletLayer as any).setStyle?.({
          fillColor: "#22d3ee",
          fillOpacity: 0.08,
          weight: 1,
          opacity: 0.5,
        });
      },
      mouseout() {
        (leafletLayer as any).setStyle?.({
          fillOpacity: 0,
          weight: 0.5,
          opacity: 0.16,
        });
      },
    });
  }

  return (
    <>
      {/* faint state borders (clickable when AOI selection enabled) */}
      {states && (
        <GeoJSON
          key={`states-${interactiveStates}`}
          data={states as any}
          style={
            (interactiveStates
              ? { ...STATES_STYLE, interactive: true, fill: true, fillOpacity: 0 }
              : STATES_STYLE) as any
          }
          onEachFeature={interactiveStates ? (onEachState as any) : undefined}
        />
      )}

      {/* districts only at higher zoom for performance */}
      {districts && zoom >= 7 && (
        <GeoJSON
          key="districts"
          data={districts as any}
          style={DISTRICTS_STYLE as any}
        />
      )}

      {/* always-on national outline (glowing) — drawn last so it reads on top */}
      {outline && (
        <GeoJSON key="outline" data={outline as any} style={OUTLINE_STYLE as any} />
      )}
    </>
  );
}

export default function MapView({
  bbox,
  layer,
  drawMode,
  onDrawComplete,
  shelters,
  route,
  onSelectState,
}: MapViewProps) {
  const aoiBounds = bboxToLeafletBounds(bbox);
  const [zoom, setZoom] = useState(9);

  // ----- choropleth styling for grid layers -----
  const gridConfig = layer ? productValueConfig(layer.product) : null;

  // For climate, scale the delta grid dynamically by its observed range.
  const dynamicRange = useMemo<[number, number] | undefined>(() => {
    if (!layer?.grid || !gridConfig) return undefined;
    if (layer.product !== "projection" && layer.product !== "anomaly")
      return gridConfig.range;
    const vals = layer.grid.features
      .map((f) => f.properties?.[gridConfig.key])
      .filter((v): v is number => typeof v === "number");
    if (!vals.length) return [0, 1];
    const lo = Math.min(...vals);
    const hi = Math.max(...vals);
    return lo === hi ? [lo - 1, hi + 1] : [lo, hi];
  }, [layer, gridConfig]);

  const isRoadRisk = layer?.product === "road_risk";

  function styleFeature(feature?: Feature): PathOptions {
    if (!feature || !layer || !gridConfig) return {};
    const props = feature.properties || {};

    if (isRoadRisk) {
      const disrupted = props.disrupted === true;
      return {
        color: disrupted ? "#ef4444" : "#3b82f6",
        weight: disrupted ? 3.5 : 2.5,
        opacity: 0.9,
      };
    }

    const value = props[gridConfig.key];
    if (typeof value !== "number") {
      return { fillOpacity: 0, opacity: 0 };
    }
    const color = valueToColor(
      value,
      layer.legend,
      dynamicRange ?? gridConfig.range,
    );
    return {
      fillColor: color,
      fillOpacity: 0.62,
      color: color,
      weight: 0.4,
      opacity: 0.5,
    };
  }

  function onEachFeature(feature: Feature, leafletLayer: LeafletLayer) {
    if (!layer || !gridConfig) return;
    const props = feature.properties || {};
    let html = "";
    if (isRoadRisk) {
      html = `<div style="font-size:12px"><b>${
        props.disrupted ? "Disrupted road" : "Passable road"
      }</b><br/>risk ${props.risk ?? "—"} · ${props.length_km ?? "—"} km</div>`;
    } else {
      const v = props[gridConfig.key];
      const label = gridConfig.key.replace(/_/g, " ");
      html = `<div style="font-size:12px"><b>${label}</b>: ${
        typeof v === "number" ? v.toFixed(3) : v
      }${
        typeof props.confidence === "number"
          ? `<br/>confidence ${props.confidence.toFixed(2)}`
          : ""
      }</div>`;
    }
    leafletLayer.bindTooltip(html, { sticky: true, opacity: 0.95 });
  }

  // Re-mount GeoJSON when the layer changes so styles refresh.
  const gridKey = layer
    ? `${layer.module}-${layer.product}-${JSON.stringify(bbox)}-${
        layer.grid?.features.length ?? 0
      }`
    : "none";

  // ----- ResilienceOR overlays -----
  const shelterPoints = useMemo(() => {
    if (!shelters?.features) return [];
    return shelters.features
      .filter((f) => f.geometry?.type === "Point")
      .map((f, i) => ({
        id: i,
        lat: f.geometry.coordinates[1],
        lon: f.geometry.coordinates[0],
        props: f.properties || {},
      }));
  }, [shelters]);

  const routeStyle: PathOptions = {
    color: "#10b981",
    weight: 3.5,
    opacity: 0.95,
    dashArray: "8 7",
    lineCap: "round",
  };

  return (
    <MapContainer
      center={[(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2]}
      zoom={9}
      zoomControl={true}
      className="h-full w-full"
      style={{ cursor: drawMode ? "crosshair" : "" }}
    >
      <ResizeFix />
      <ZoomWatcher onZoom={setZoom} />
      <TileLayer
        url={DARK_BASEMAP.url}
        attribution={DARK_BASEMAP.attribution}
        subdomains={["a", "b", "c", "d"]}
      />

      {/* India boundary base layers — always behind analysis */}
      <IndiaBoundaries zoom={zoom} onSelectState={onSelectState} />

      {/* live tile overlay */}
      {layer?.tile_url && (
        <TileLayer
          key={layer.tile_url}
          url={layer.tile_url}
          opacity={0.8}
        />
      )}

      {/* grid / vector layer */}
      {layer?.grid && (
        <GeoJSON
          key={gridKey}
          data={layer.grid as any}
          style={styleFeature as any}
          onEachFeature={onEachFeature as any}
        />
      )}

      {/* ResilienceOR — evacuation route (emerald, dashed) */}
      {route?.features?.length ? (
        <GeoJSON
          key={`route-${route.features.length}-${JSON.stringify(bbox)}`}
          data={route as any}
          style={routeStyle as any}
        />
      ) : null}

      {/* ResilienceOR — shelter sites (cyan markers) */}
      {shelterPoints.map((s) => (
        <CircleMarker
          key={`shelter-${s.id}-${s.lat}-${s.lon}`}
          center={[s.lat, s.lon]}
          radius={7}
          pathOptions={{
            color: "#0e7490",
            weight: 2,
            fillColor: "#22d3ee",
            fillOpacity: 0.95,
          }}
        >
          <LeafletTooltip direction="top" offset={[0, -6]} opacity={0.95}>
            <span style={{ fontSize: 12 }}>
              <b>Shelter {String(s.props.id ?? s.id + 1)}</b>
              {typeof s.props.covers === "number"
                ? ` · covers ${s.props.covers}`
                : ""}
            </span>
          </LeafletTooltip>
        </CircleMarker>
      ))}

      {/* AOI outline */}
      <Rectangle
        bounds={aoiBounds}
        pathOptions={{
          color: "#22d3ee",
          weight: 1.5,
          fillOpacity: 0,
          dashArray: "6 6",
        }}
      />

      <FlyToBounds bounds={aoiBounds} />
      <DrawHandler active={drawMode} onComplete={onDrawComplete} />
    </MapContainer>
  );
}
