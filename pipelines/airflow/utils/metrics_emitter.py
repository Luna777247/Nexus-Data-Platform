"""
Prometheus Metrics Emitter for Nexus Data Platform
Sends metrics to Prometheus Push Gateway
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class MetricsEmitter:
    """
    Emit metrics to Prometheus Push Gateway
    Used by Spark jobs and APIs to expose metrics
    """
    
    def __init__(
        self,
        job_name: str,
        pushgateway_url: Optional[str] = None,
        instance_name: Optional[str] = None
    ):
        """
        Initialize Metrics Emitter
        
        Args:
            job_name: Name of the job (e.g., "bronze_to_silver")
            pushgateway_url: Prometheus Push Gateway URL
            instance_name: Instance identifier
        """
        self.job_name = job_name
        self.pushgateway_url = pushgateway_url or os.getenv(
            "PROMETHEUS_PUSHGATEWAY",
            "http://prometheus:9091"
        )
        self.instance_name = instance_name or os.getenv("HOSTNAME", "unknown")
        self.metrics_buffer = []
    
    def emit_counter(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: Optional[str] = None
    ):
        """
        Emit a counter metric
        
        Args:
            metric_name: Metric name (e.g., "records_processed_total")
            value: Metric value
            labels: Additional labels
            help_text: Metric description
        """
        self._add_metric(
            metric_name=metric_name,
            metric_type="counter",
            value=value,
            labels=labels,
            help_text=help_text
        )
    
    def emit_gauge(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: Optional[str] = None
    ):
        """
        Emit a gauge metric
        
        Args:
            metric_name: Metric name (e.g., "kafka_lag_seconds")
            value: Metric value
            labels: Additional labels
            help_text: Metric description
        """
        self._add_metric(
            metric_name=metric_name,
            metric_type="gauge",
            value=value,
            labels=labels,
            help_text=help_text
        )
    
    def emit_histogram(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: Optional[str] = None
    ):
        """
        Emit a histogram metric
        
        Args:
            metric_name: Metric name (e.g., "job_duration_seconds")
            value: Metric value
            labels: Additional labels
            help_text: Metric description
        """
        self._add_metric(
            metric_name=metric_name,
            metric_type="histogram",
            value=value,
            labels=labels,
            help_text=help_text
        )
    
    def _add_metric(
        self,
        metric_name: str,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: Optional[str] = None
    ):
        """Add metric to buffer"""
        metric = {
            "name": metric_name,
            "type": metric_type,
            "value": value,
            "labels": labels or {},
            "help": help_text or f"{metric_name} metric",
            "timestamp": datetime.now().timestamp() * 1000  # milliseconds
        }
        
        self.metrics_buffer.append(metric)
        logger.debug(f"📊 Buffered metric: {metric_name}={value}")
    
    def push_metrics(self) -> bool:
        """
        Push all buffered metrics to Prometheus Push Gateway
        
        Returns:
            True if successful, False otherwise
        """
        if not self.metrics_buffer:
            logger.info("ℹ️ No metrics to push")
            return True
        
        try:
            # Convert metrics to Prometheus text format
            prometheus_text = self._convert_to_prometheus_format()
            
            # Push to Push Gateway
            url = f"{self.pushgateway_url}/metrics/job/{self.job_name}/instance/{self.instance_name}"
            
            response = requests.post(
                url,
                data=prometheus_text,
                headers={"Content-Type": "text/plain; version=0.0.4"},
                timeout=10
            )
            
            if response.status_code in [200, 202]:
                logger.info(
                    f"✅ Pushed {len(self.metrics_buffer)} metrics to Prometheus"
                )
                self.metrics_buffer.clear()
                return True
            else:
                logger.error(
                    f"❌ Failed to push metrics: HTTP {response.status_code}"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to Prometheus Push Gateway: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error pushing metrics: {e}")
            return False
    
    def _convert_to_prometheus_format(self) -> str:
        """
        Convert buffered metrics to Prometheus text format
        
        Returns:
            Prometheus format string
        """
        lines = []
        
        for metric in self.metrics_buffer:
            # Add HELP line
            if metric["help"]:
                lines.append(f"# HELP {metric['name']} {metric['help']}")
            
            # Add TYPE line
            lines.append(f"# TYPE {metric['name']} {metric['type']}")
            
            # Build labels string
            labels = metric.get("labels", {})
            labels_str = ""
            if labels:
                label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
                labels_str = "{" + ",".join(label_pairs) + "}"
            
            # Add metric value
            lines.append(f"{metric['name']}{labels_str} {metric['value']}")
        
        return "\n".join(lines) + "\n"
    
    def emit_job_metrics(
        self,
        duration_seconds: float,
        records_processed: int,
        records_failed: int,
        status: str
    ):
        """
        Convenience method to emit standard job metrics
        
        Args:
            duration_seconds: Job duration
            records_processed: Number of records processed
            records_failed: Number of failed records
            status: Job status (success/failed)
        """
        labels = {"job": self.job_name, "status": status}
        
        self.emit_histogram(
            "job_duration_seconds",
            duration_seconds,
            labels=labels,
            help_text="Job execution duration in seconds"
        )
        
        self.emit_counter(
            "records_processed_total",
            records_processed,
            labels=labels,
            help_text="Total number of records processed"
        )
        
        self.emit_counter(
            "records_failed_total",
            records_failed,
            labels=labels,
            help_text="Total number of failed records"
        )
        
        # Success rate
        if records_processed > 0:
            success_rate = (records_processed - records_failed) / records_processed * 100
            self.emit_gauge(
                "job_success_rate_percent",
                success_rate,
                labels=labels,
                help_text="Job success rate percentage"
            )
    
    def emit_data_quality_metrics(
        self,
        quality_score: float,
        layer: str,
        failed_checks: int,
        total_checks: int
    ):
        """
        Convenience method to emit data quality metrics
        
        Args:
            quality_score: Quality score (0-100)
            layer: Data layer (bronze/silver/gold)
            failed_checks: Number of failed quality checks
            total_checks: Total number of quality checks
        """
        labels = {"layer": layer, "job": self.job_name}
        
        self.emit_gauge(
            "data_quality_score",
            quality_score,
            labels=labels,
            help_text="Data quality score (0-100)"
        )
        
        self.emit_counter(
            "quality_checks_failed_total",
            failed_checks,
            labels=labels,
            help_text="Total failed quality checks"
        )
        
        self.emit_counter(
            "quality_checks_total",
            total_checks,
            labels=labels,
            help_text="Total quality checks performed"
        )
    
    def emit_kafka_lag_metrics(
        self,
        topic: str,
        consumer_group: str,
        lag_messages: int,
        lag_seconds: float
    ):
        """
        Emit Kafka consumer lag metrics
        
        Args:
            topic: Kafka topic name
            consumer_group: Consumer group name
            lag_messages: Lag in number of messages
            lag_seconds: Lag in seconds
        """
        labels = {
            "topic": topic,
            "consumer_group": consumer_group
        }
        
        self.emit_gauge(
            "kafka_consumer_lag_messages",
            lag_messages,
            labels=labels,
            help_text="Kafka consumer lag in number of messages"
        )
        
        self.emit_gauge(
            "kafka_consumer_lag_seconds",
            lag_seconds,
            labels=labels,
            help_text="Kafka consumer lag in seconds"
        )


# Example usage in Spark job:
"""
from utils.metrics_emitter import MetricsEmitter
import time

# Initialize metrics emitter
metrics = MetricsEmitter(job_name="bronze_to_silver")

# Record job start
start_time = time.time()

# ... do work ...

# Record metrics
duration = time.time() - start_time
metrics.emit_job_metrics(
    duration_seconds=duration,
    records_processed=1000,
    records_failed=10,
    status="success"
)

# Push to Prometheus
metrics.push_metrics()
"""
