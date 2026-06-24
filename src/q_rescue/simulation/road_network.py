"""Realistic road-network routing using OSMnx and NetworkX.

This module downloads and caches the Sheffield drive network. If the optional
``osmnx`` dependency is missing, it gracefully degrades to Haversine
(great-circle) distance.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from q_rescue.domain.models import Location
from q_rescue.simulation.sheffield import haversine_distance

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    import osmnx as ox

    HAS_OSMNX = True
except ImportError:
    HAS_OSMNX = False


class SheffieldRoadNetwork:
    """Road network distance calculator for Sheffield.

    On first run, downloads the "drive" network graph for Sheffield.
    Subsequent runs load the graph from the local cache.
    """

    def __init__(self, cache_dir: str | Path | None = None):
        if cache_dir is None:
            # Default to data/road_network_cache in project root
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            self.cache_dir = project_root / "data" / "road_network_cache"
        else:
            self.cache_dir = Path(cache_dir)

        self.graph_path = self.cache_dir / "sheffield_drive.graphml"
        self._graph: Any = None

    def load(self) -> None:
        """Load the network graph. Downloads it if not cached.

        Raises:
            ImportError: If osmnx is not installed.
        """
        if not HAS_OSMNX:
            raise ImportError(
                "osmnx is required for road network routing. Install with: pip install '.[geo]'"
            )

        if self._graph is not None:
            return  # Already loaded

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if self.graph_path.exists():
            logger.info("Loading Sheffield road network from cache...")
            self._graph = ox.load_graphml(self.graph_path)
        else:
            logger.info("Downloading Sheffield road network (this may take a minute)...")
            ox.settings.use_cache = True
            ox.settings.log_console = True

            # Download graph for Sheffield, UK
            self._graph = ox.graph_from_place(
                "Sheffield, South Yorkshire, England", network_type="drive"
            )

            logger.info(f"Saving graph to {self.graph_path}...")
            ox.save_graphml(self._graph, self.graph_path)

    def shortest_path_distance(self, origin: Location, destination: Location) -> float:
        """Calculate the shortest path distance in km using the road network.

        Falls back to Haversine distance if osmnx is not installed or
        if a route cannot be found.
        """
        if not HAS_OSMNX:
            return haversine_distance(origin, destination)

        if self._graph is None:
            self.load()

        try:
            # Find nearest nodes in the graph
            orig_node = ox.distance.nearest_nodes(self._graph, origin.y, origin.x)
            dest_node = ox.distance.nearest_nodes(self._graph, destination.y, destination.x)

            # Calculate shortest path length (in metres)
            length_m = nx.shortest_path_length(self._graph, orig_node, dest_node, weight="length")
            return length_m / 1000.0

        except Exception as e:
            logger.warning(
                f"Failed to find route between {origin} and {destination}: {e}. "
                "Falling back to Haversine distance."
            )
            return haversine_distance(origin, destination)

    def travel_time_minutes(
        self, origin: Location, destination: Location, speed_kmh: float = 50.0
    ) -> float:
        """Estimate travel time in minutes based on distance and average speed."""
        distance_km = self.shortest_path_distance(origin, destination)
        hours = distance_km / speed_kmh
        return hours * 60.0
