#!/usr/bin/env python3
import time
from typing import Dict, Any
from threading import Lock

class MetricsCollector:
    """Collector for processing metrics and statistics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self._metrics = {}
        self._counters = {}
        self._start_time = time.monotonic()
        self._lock = Lock()
    
    def update(self, metrics: Dict[str, Any]):
        """
        Update multiple metrics.
        
        Args:
            metrics: Dictionary of metric names and values
        """
        with self._lock:
            self._metrics.update(metrics)
    
    def set(self, name: str, value: Any):
        """
        Set a single metric.
        
        Args:
            name: Metric name
            value: Metric value
        """
        with self._lock:
            self._metrics[name] = value
    
    def increment(self, name: str, amount: int = 1):
        """
        Increment a counter.
        
        Args:
            name: Counter name
            amount: Amount to increment by
        """
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount
    
    def get(self, name: str, default: Any = None) -> Any:
        """
        Get a metric value.
        
        Args:
            name: Metric name
            default: Default value if metric doesn't exist
            
        Returns:
            Metric value
        """
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            if name in self._counters:
                return self._counters[name]
            return default
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all metrics and counters.
        
        Returns:
            Dict: Combined metrics and counters
        """
        with self._lock:
            metrics = self._metrics.copy()
            metrics.update(self._counters)
            metrics['uptime'] = time.monotonic() - self._start_time
            return metrics
    
    def reset(self):
        """Reset all metrics and counters."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._start_time = time.monotonic() 