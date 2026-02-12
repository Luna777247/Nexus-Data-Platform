"""
Data Lineage Tracker using OpenMetadata API
Tracks data flow across Bronze → Silver → Gold layers
"""

import requests
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class LineageTracker:
    """
    Track data lineage using OpenMetadata
    Records transformations, sources, and destinations
    """
    
    def __init__(self, openmetadata_url: Optional[str] = None):
        """
        Initialize Lineage Tracker
        
        Args:
            openmetadata_url: OpenMetadata server URL
        """
        self.openmetadata_url = openmetadata_url or os.getenv(
            "OPENMETADATA_URL", 
            "http://openmetadata:8585"
        )
        self.api_version = "v1"
        self.base_url = f"{self.openmetadata_url}/api/{self.api_version}"
        self.lineage_events = []
        
    def track_ingestion(
        self,
        source_name: str,
        source_type: str,
        destination: str,
        row_count: int,
        metadata: Optional[Dict] = None
    ):
        """
        Track data ingestion event
        
        Args:
            source_name: Source system name (e.g., "topic_app_events")
            source_type: Type of source (kafka/cdc/api)
            destination: Bronze layer path
            row_count: Number of rows ingested
            metadata: Additional metadata
        """
        event = {
            "event_type": "ingestion",
            "timestamp": datetime.now().isoformat(),
            "source": {
                "name": source_name,
                "type": source_type
            },
            "destination": {
                "layer": "bronze",
                "path": destination
            },
            "metrics": {
                "row_count": row_count
            },
            "metadata": metadata or {}
        }
        
        self.lineage_events.append(event)
        logger.info(f"📊 Tracked ingestion: {source_name} → {destination} ({row_count} rows)")
        
        # Send to OpenMetadata (if available)
        self._send_to_openmetadata(event)
    
    def track_transformation(
        self,
        job_name: str,
        source_layer: str,
        source_tables: List[str],
        destination_layer: str,
        destination_table: str,
        transformation_type: str,
        row_count_in: int,
        row_count_out: int,
        metadata: Optional[Dict] = None
    ):
        """
        Track data transformation event
        
        Args:
            job_name: Name of the transformation job
            source_layer: Source layer (bronze/silver)
            source_tables: List of source table paths
            destination_layer: Destination layer (silver/gold)
            destination_table: Destination table path
            transformation_type: Type of transformation (cleaning/aggregation)
            row_count_in: Input row count
            row_count_out: Output row count
            metadata: Additional metadata
        """
        event = {
            "event_type": "transformation",
            "timestamp": datetime.now().isoformat(),
            "job_name": job_name,
            "source": {
                "layer": source_layer,
                "tables": source_tables
            },
            "destination": {
                "layer": destination_layer,
                "table": destination_table
            },
            "transformation_type": transformation_type,
            "metrics": {
                "row_count_in": row_count_in,
                "row_count_out": row_count_out,
                "data_loss_percentage": (
                    (row_count_in - row_count_out) / row_count_in * 100 
                    if row_count_in > 0 else 0
                )
            },
            "metadata": metadata or {}
        }
        
        self.lineage_events.append(event)
        logger.info(
            f"📊 Tracked transformation: {source_layer} → {destination_layer} "
            f"({row_count_in} → {row_count_out} rows)"
        )
        
        # Send to OpenMetadata
        self._send_to_openmetadata(event)
    
    def track_job_start(
        self,
        job_name: str,
        job_type: str,
        parameters: Optional[Dict] = None
    ):
        """
        Track job start event
        
        Args:
            job_name: Name of the job (e.g., "bronze_to_silver")
            job_type: Type of job (etl/ingestion/aggregation)
            parameters: Job parameters
        """
        event = {
            "event_type": "job_start",
            "timestamp": datetime.now().isoformat(),
            "job_name": job_name,
            "job_type": job_type,
            "parameters": parameters or {}
        }
        
        self.lineage_events.append(event)
        logger.info(f"▶️ Job started: {job_name}")
        
        self._send_to_openmetadata(event)
    
    def track_job_end(
        self,
        job_name: str,
        status: str,
        duration_seconds: float,
        error: Optional[str] = None
    ):
        """
        Track job completion event
        
        Args:
            job_name: Name of the job
            status: Job status (success/failed)
            duration_seconds: Job duration
            error: Error message if failed
        """
        event = {
            "event_type": "job_end",
            "timestamp": datetime.now().isoformat(),
            "job_name": job_name,
            "status": status,
            "metrics": {
                "duration_seconds": duration_seconds
            },
            "error": error
        }
        
        self.lineage_events.append(event)
        
        status_icon = "✅" if status == "success" else "❌"
        logger.info(
            f"{status_icon} Job ended: {job_name} - {status} "
            f"({duration_seconds:.2f}s)"
        )
        
        self._send_to_openmetadata(event)
    
    def track_api_request(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int
    ):
        """
        Track API request for serving layer lineage
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
        """
        event = {
            "event_type": "api_request",
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "metrics": {
                "response_time_ms": response_time_ms,
                "status_code": status_code
            }
        }
        
        self.lineage_events.append(event)
        logger.debug(f"🌐 API: {method} {endpoint} - {status_code} ({response_time_ms}ms)")
        
        # Don't send every API request to OpenMetadata (too noisy)
        # Only track in local events for metrics
    
    def _send_to_openmetadata(self, event: Dict):
        """
        Send lineage event to OpenMetadata
        
        Args:
            event: Lineage event dict
        """
        try:
            # OpenMetadata lineage API endpoint
            url = f"{self.base_url}/lineage"
            
            # Transform event to OpenMetadata format
            payload = self._transform_to_openmetadata_format(event)
            
            # Send HTTP POST
            response = requests.post(
                url,
                json=payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                logger.debug(f"✅ Lineage sent to OpenMetadata: {event['event_type']}")
            else:
                logger.warning(
                    f"⚠️ Failed to send lineage to OpenMetadata: "
                    f"Status {response.status_code}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Could not connect to OpenMetadata: {e}")
        except Exception as e:
            logger.error(f"❌ Error sending lineage: {e}")
    
    def _transform_to_openmetadata_format(self, event: Dict) -> Dict:
        """
        Transform internal event format to OpenMetadata API format
        
        Args:
            event: Internal event dict
            
        Returns:
            OpenMetadata-compatible payload
        """
        # Simplified transformation - actual implementation would be more complex
        # This is a placeholder for the real OpenMetadata API format
        
        payload = {
            "edge": {
                "fromEntity": {
                    "id": event.get("source", {}).get("name", "unknown"),
                    "type": "table"
                },
                "toEntity": {
                    "id": event.get("destination", {}).get("table", "unknown"),
                    "type": "table"
                }
            },
            "description": f"{event.get('event_type')} event",
            "pipeline": {
                "name": event.get("job_name", "unknown"),
                "type": "Spark"
            }
        }
        
        return payload
    
    def emit_metrics(self) -> Dict:
        """
        Emit lineage metrics for Prometheus
        
        Returns:
            Metrics dict
        """
        total_events = len(self.lineage_events)
        
        event_counts = {}
        for event in self.lineage_events:
            event_type = event.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        metrics = {
            "total_lineage_events": total_events,
            "event_breakdown": event_counts,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Lineage events tracked: {total_events}")
        return metrics
    
    def generate_lineage_graph(self) -> Dict:
        """
        Generate lineage graph from tracked events
        
        Returns:
            Graph representation of data lineage
        """
        nodes = set()
        edges = []
        
        for event in self.lineage_events:
            if event["event_type"] == "transformation":
                source = event["source"]
                destination = event["destination"]
                
                # Add nodes
                for table in source.get("tables", []):
                    nodes.add((source["layer"], table))
                
                nodes.add((destination["layer"], destination["table"]))
                
                # Add edges
                for table in source.get("tables", []):
                    edges.append({
                        "from": f"{source['layer']}/{table}",
                        "to": f"{destination['layer']}/{destination['table']}",
                        "job": event["job_name"]
                    })
        
        return {
            "nodes": [{"layer": layer, "table": table} for layer, table in nodes],
            "edges": edges
        }
