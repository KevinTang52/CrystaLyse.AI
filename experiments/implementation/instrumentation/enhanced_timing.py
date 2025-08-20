"""
Enhanced timing infrastructure for CrystaLyse experiments.
Captures comprehensive timing data with tool-level granularity.
"""

import time
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolTiming:
    """Individual tool call timing data."""
    tool_name: str
    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool = True
    error: Optional[str] = None
    cache_hit: bool = False
    attempt: int = 1
    timeout_s: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

@dataclass 
class QueryTiming:
    """Complete query execution timing."""
    query_id: str
    query_text: str
    mode: str
    total_start: float
    total_end: float = 0
    time_to_first_result: Optional[float] = None
    validator_overhead_s: float = 0
    tool_timings: List[ToolTiming] = field(default_factory=list)
    
    @property
    def total_duration(self) -> float:
        """Total query duration in seconds."""
        return self.total_end - self.total_start if self.total_end else 0
    
    @property
    def tool_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Breakdown of timing by tool and operation."""
        breakdown = {}
        for timing in self.tool_timings:
            key = f"{timing.tool_name}_{timing.operation}"
            if key not in breakdown:
                breakdown[key] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "cache_hits": 0,
                    "failures": 0,
                    "max_time": 0,
                    "min_time": float('inf')
                }
            
            stats = breakdown[key]
            stats["count"] += 1
            stats["total_time"] += timing.duration
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["max_time"] = max(stats["max_time"], timing.duration)
            stats["min_time"] = min(stats["min_time"], timing.duration)
            
            if timing.cache_hit:
                stats["cache_hits"] += 1
            if not timing.success:
                stats["failures"] += 1
                
        return breakdown
    
    def to_event_json(self) -> Dict[str, Any]:
        """Convert to JSONL event format."""
        query_hash = hashlib.sha256(self.query_text.encode()).hexdigest()[:8]
        
        return {
            "run_id": f"r-{datetime.fromtimestamp(self.total_start):%Y%m%dT%H%M%SZ}",
            "task_id": self.query_id,
            "mode": self.mode,
            "prompt_sha": query_hash,
            "ts_start": datetime.fromtimestamp(self.total_start).isoformat(),
            "ts_end": datetime.fromtimestamp(self.total_end).isoformat() if self.total_end else None,
            "total_s": self.total_duration,
            "time_to_first_s": self.time_to_first_result,
            "validator_overhead_s": self.validator_overhead_s,
            "tool_calls": len(self.tool_timings),
            "tools": [
                {
                    "call_id": f"{t.tool_name}-{i:04d}",
                    "tool": t.tool_name,
                    "op": t.operation,
                    "start": datetime.fromtimestamp(t.start_time).isoformat(),
                    "end": datetime.fromtimestamp(t.end_time).isoformat(),
                    "dur_s": t.duration,
                    "status": "ok" if t.success else "error",
                    "error": t.error,
                    "attempt": t.attempt,
                    "timeout_s": t.timeout_s,
                    "cache": t.cache_hit,
                    "metadata": t.metadata
                }
                for i, t in enumerate(self.tool_timings)
            ]
        }

class EnhancedTimingLogger:
    """Comprehensive timing logger for experiments."""
    
    def __init__(self, experiment_name: str, output_dir: Optional[Path] = None):
        self.experiment_name = experiment_name
        self.queries: List[QueryTiming] = []
        self.current_query: Optional[QueryTiming] = None
        
        # Setup output paths
        if output_dir is None:
            output_dir = Path("experiments")
        self.output_dir = Path(output_dir)
        
        # Create directories
        self.raw_data_dir = self.output_dir / "raw_data" / "events"
        self.processed_data_dir = self.output_dir / "processed_data"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Event log path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.event_log_path = self.raw_data_dir / f"run_{experiment_name}_{timestamp}.jsonl"
        
        logger.info(f"TimingLogger initialized: {self.event_log_path}")
    
    @contextmanager
    def time_query(self, query_id: str, query_text: str, mode: str):
        """Context manager for timing complete queries."""
        self.current_query = QueryTiming(
            query_id=query_id,
            query_text=query_text,
            mode=mode,
            total_start=time.time()
        )
        
        try:
            yield self.current_query
        finally:
            self.current_query.total_end = time.time()
            self.queries.append(self.current_query)
            self._write_event()
            logger.info(f"Query {query_id} completed in {self.current_query.total_duration:.2f}s")
    
    @contextmanager
    def time_tool(self, tool_name: str, operation: str, **metadata):
        """Context manager for timing individual tool calls."""
        if not self.current_query:
            raise ValueError("No active query context for tool timing")
        
        start = time.time()
        timing = ToolTiming(
            tool_name=tool_name,
            operation=operation,
            start_time=start,
            end_time=0,
            duration=0,
            metadata=metadata,
            timeout_s=metadata.get('timeout_s'),
            attempt=metadata.get('attempt', 1)
        )
        
        try:
            yield timing
            timing.success = True
            
            # Mark time to first result if this is the first successful tool
            if (self.current_query.time_to_first_result is None and 
                timing.success):
                self.current_query.time_to_first_result = time.time() - self.current_query.total_start
                
        except Exception as e:
            timing.success = False
            timing.error = str(e)
            logger.warning(f"Tool {tool_name}.{operation} failed: {e}")
            raise
        finally:
            timing.end_time = time.time()
            timing.duration = timing.end_time - timing.start_time
            self.current_query.tool_timings.append(timing)
            
            logger.debug(f"Tool {tool_name}.{operation}: {timing.duration:.3f}s")
    
    def add_validator_overhead(self, overhead_seconds: float):
        """Add validator overhead to current query."""
        if self.current_query:
            self.current_query.validator_overhead_s += overhead_seconds
    
    def _write_event(self):
        """Write current query as JSONL event."""
        if not self.current_query:
            return
            
        try:
            with open(self.event_log_path, 'a') as f:
                json.dump(self.current_query.to_event_json(), f)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to write event: {e}")
    
    def export_analysis(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Export comprehensive timing analysis to CSV files."""
        if not self.queries:
            logger.warning("No queries to analyze")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Tool-level data
        tool_rows = []
        for q in self.queries:
            for t in q.tool_timings:
                tool_rows.append({
                    'experiment': self.experiment_name,
                    'run_id': f"{self.experiment_name}_{q.query_id}",
                    'task_id': q.query_id,
                    'mode': q.mode,
                    'tool': t.tool_name,
                    'operation': t.operation,
                    'attempt': t.attempt,
                    'status': 'ok' if t.success else 'error',
                    'duration_s': t.duration,
                    'timeout_s': t.timeout_s,
                    'cache_hit': t.cache_hit,
                    'error': t.error,
                    'ts_start': datetime.fromtimestamp(t.start_time).isoformat(),
                    **t.metadata  # Include all metadata
                })
        
        # Task-level data
        task_rows = []
        for q in self.queries:
            task_rows.append({
                'experiment': self.experiment_name,
                'run_id': f"{self.experiment_name}_{q.query_id}",
                'task_id': q.query_id,
                'mode': q.mode,
                'query_hash': hashlib.sha256(q.query_text.encode()).hexdigest()[:8],
                'total_time_s': q.total_duration,
                'time_to_first_result_s': q.time_to_first_result,
                'validator_overhead_s': q.validator_overhead_s,
                'tool_calls': len(q.tool_timings),
                'successful_tools': sum(1 for t in q.tool_timings if t.success),
                'failed_tools': sum(1 for t in q.tool_timings if not t.success),
                'cache_hits': sum(1 for t in q.tool_timings if t.cache_hit),
                'ts_start': datetime.fromtimestamp(q.total_start).isoformat()
            })
        
        # Create DataFrames
        tool_df = pd.DataFrame(tool_rows)
        task_df = pd.DataFrame(task_rows)
        
        # Percentile analysis
        if not tool_df.empty:
            percentiles = tool_df.groupby(['tool', 'operation'])['duration_s'].agg([
                'count', 'mean', 'std', 'min', 'max',
                lambda x: x.quantile(0.5),   # median
                lambda x: x.quantile(0.9),   # p90
                lambda x: x.quantile(0.99),  # p99
            ])
            percentiles.columns = ['count', 'mean', 'std', 'min', 'max', 'p50', 'p90', 'p99']
            
            # Add success rates
            success_rates = tool_df.groupby(['tool', 'operation'])['status'].apply(
                lambda x: (x == 'ok').mean()
            ).rename('success_rate')
            percentiles = percentiles.join(success_rates)
        else:
            percentiles = pd.DataFrame()
        
        # Save to CSV
        tool_csv = self.processed_data_dir / f"timing_by_tool_{self.experiment_name}.csv"
        task_csv = self.processed_data_dir / f"timing_by_task_{self.experiment_name}.csv"
        percentiles_csv = self.processed_data_dir / f"timing_percentiles_{self.experiment_name}.csv"
        
        tool_df.to_csv(tool_csv, index=False)
        task_df.to_csv(task_csv, index=False)
        percentiles.to_csv(percentiles_csv)
        
        logger.info(f"Timing analysis exported:")
        logger.info(f"  Tools: {tool_csv}")
        logger.info(f"  Tasks: {task_csv}")
        logger.info(f"  Percentiles: {percentiles_csv}")
        
        return tool_df, task_df, percentiles
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for current experiment."""
        if not self.queries:
            return {}
        
        total_queries = len(self.queries)
        total_tools = sum(len(q.tool_timings) for q in self.queries)
        successful_queries = sum(1 for q in self.queries if q.total_end > 0)
        
        durations = [q.total_duration for q in self.queries if q.total_end > 0]
        tool_durations = [t.duration for q in self.queries for t in q.tool_timings]
        
        return {
            "experiment": self.experiment_name,
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "total_tool_calls": total_tools,
            "query_duration_stats": {
                "mean": sum(durations) / len(durations) if durations else 0,
                "min": min(durations) if durations else 0,
                "max": max(durations) if durations else 0
            },
            "tool_duration_stats": {
                "mean": sum(tool_durations) / len(tool_durations) if tool_durations else 0,
                "min": min(tool_durations) if tool_durations else 0,
                "max": max(tool_durations) if tool_durations else 0
            },
            "timestamp": datetime.now().isoformat()
        }

# Convenience function for easy integration
def time_crystalyse_operation(timer: EnhancedTimingLogger, query_id: str, query: str, mode: str):
    """Convenience function for timing CrystaLyse operations."""
    return timer.time_query(query_id, query, mode)