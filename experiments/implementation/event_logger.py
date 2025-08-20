"""
JSONL event logging system for CrystaLyse experiments.
Provides immediate event writes with CSV aggregation capabilities.
"""

import json
import time
import uuid
import glob as g
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class EventLogger:
    """Event logger that writes JSONL immediately for real-time monitoring."""
    
    def __init__(self, run_id: Optional[str] = None, output_dir: Optional[Path] = None):
        self.run_id = run_id or f"r-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
        
        # Setup output directory
        if output_dir is None:
            output_dir = Path("experiments")
        self.output_dir = Path(output_dir)
        self.events_dir = self.output_dir / "raw_data" / "events"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        # Event log file
        self.path = self.events_dir / f"{self.run_id}.jsonl"
        
        # Write initial metadata
        self._log_initial_metadata()
        logger.info(f"EventLogger initialized: {self.path}")
    
    def _log_initial_metadata(self):
        """Log initial run metadata."""
        metadata = {
            "run_id": self.run_id,
            "event_type": "run_start",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "CrystaLyse-v2.0-alpha",
            "logger_version": "1.0"
        }
        self._write_event(metadata)
    
    @contextmanager
    def log_call(self, tool: str, operation: str, **metadata):
        """Context manager for logging tool calls with timing."""
        call_id = f"{tool}-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        status = "ok"
        error = None
        result_summary = {}
        
        try:
            yield call_id
            
        except Exception as e:
            status = "error"
            error = str(e)
            logger.warning(f"Tool call {call_id} failed: {e}")
            raise
            
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Log the completed call
            call_event = {
                "run_id": self.run_id,
                "call_id": call_id,
                "event_type": "tool_call",
                "tool": tool,
                "operation": operation,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_s": duration,
                "status": status,
                "error": error,
                **metadata  # Include all passed metadata
            }
            self._write_event(call_event)
    
    def log_task_summary(self, task_id: str, mode: str, **fields):
        """Log task-level summary information."""
        summary_event = {
            "run_id": self.run_id,
            "event_type": "task_summary",
            "task_id": task_id,
            "mode": mode,
            "timestamp": datetime.utcnow().isoformat(),
            **fields
        }
        self._write_event(summary_event)
    
    def log_agent_insight(self, category: str, insight: str, **context):
        """Log agent insights and discoveries."""
        insight_event = {
            "run_id": self.run_id,
            "event_type": "agent_insight",
            "category": category,
            "insight": insight,
            "timestamp": datetime.utcnow().isoformat(),
            **context
        }
        self._write_event(insight_event)
    
    def log_validation_event(self, validation_type: str, result: Dict[str, Any]):
        """Log validation events (provenance, hallucination detection, etc.)."""
        validation_event = {
            "run_id": self.run_id,
            "event_type": "validation",
            "validation_type": validation_type,
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
        self._write_event(validation_event)
    
    def log_experiment_checkpoint(self, phase: str, status: str, **metadata):
        """Log experimental phase checkpoints."""
        checkpoint_event = {
            "run_id": self.run_id,
            "event_type": "checkpoint",
            "phase": phase,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            **metadata
        }
        self._write_event(checkpoint_event)
    
    def _write_event(self, event: Dict[str, Any]):
        """Write single event to JSONL file."""
        try:
            with open(self.path, 'a') as f:
                json.dump(event, f, default=str)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to write event: {e}")
    
    def close(self):
        """Close the event logger."""
        final_event = {
            "run_id": self.run_id,
            "event_type": "run_end",
            "timestamp": datetime.utcnow().isoformat()
        }
        self._write_event(final_event)

def aggregate_jsonl_to_csv(
    glob_pattern: str = "experiments/raw_data/events/*.jsonl",
    output_dir: Optional[Path] = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate JSONL event files to CSV for analysis."""
    
    if output_dir is None:
        output_dir = Path("experiments/processed_data")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all events
    rows = []
    files_processed = 0
    
    for file_path in g.glob(glob_pattern):
        try:
            with open(file_path) as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        event = json.loads(line.strip())
                        event['source_file'] = Path(file_path).name
                        event['line_number'] = line_num
                        rows.append(event)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON at {file_path}:{line_num}: {e}")
            files_processed += 1
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    if not rows:
        logger.warning("No events found to aggregate")
        return pd.DataFrame(), pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    logger.info(f"Aggregated {len(rows)} events from {files_processed} files")
    
    # Separate tool calls and task summaries
    tool_calls = df[df.event_type == "tool_call"].copy() if 'event_type' in df.columns else pd.DataFrame()
    task_summaries = df[df.event_type == "task_summary"].copy() if 'event_type' in df.columns else pd.DataFrame()
    
    # Save to CSV
    if not tool_calls.empty:
        tool_calls_path = output_dir / "timing_by_tool.csv"
        tool_calls.to_csv(tool_calls_path, index=False)
        logger.info(f"Tool calls saved: {tool_calls_path}")
    
    if not task_summaries.empty:
        task_summaries_path = output_dir / "timing_by_task.csv"  
        task_summaries.to_csv(task_summaries_path, index=False)
        logger.info(f"Task summaries saved: {task_summaries_path}")
    
    # Save full event log
    full_events_path = output_dir / "all_events.csv"
    df.to_csv(full_events_path, index=False)
    logger.info(f"All events saved: {full_events_path}")
    
    return tool_calls, task_summaries

class AgentInsightLogger:
    """Specialized logger for capturing agent insights during experiments."""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.insights_file = Path("experiments/logs/agent_findings.md")
        self.insights_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if it doesn't exist
        if not self.insights_file.exists():
            self._initialize_insights_file()
    
    def _initialize_insights_file(self):
        """Initialize the insights markdown file."""
        header = f"""# Agent Research Findings - {self.experiment_name}

**Experiment Start**: {datetime.now().isoformat()}
**Agent**: Claude Code (Sonnet 4)  
**Environment**: CrystaLyse.AI v2.0-alpha
**Objective**: Generate real experimental results for paper validation

## Key Insights

## Technical Observations

## Performance Patterns  

## Interesting Discoveries

## Implementation Notes

---
*This log is automatically updated during experiments*
"""
        self.insights_file.write_text(header)
    
    def log_insight(
        self, 
        category: str, 
        title: str, 
        content: str, 
        context: Optional[Dict[str, Any]] = None
    ):
        """Add an insight to the markdown log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        insight_entry = f"""
### {title} [{category}]
**Time**: {timestamp}
{content}
"""
        
        if context:
            insight_entry += f"\n**Context**: {json.dumps(context, indent=2)}\n"
        
        insight_entry += "\n---\n"
        
        # Append to file
        with open(self.insights_file, 'a') as f:
            f.write(insight_entry)
        
        logger.info(f"Agent insight logged: {title}")
    
    def log_performance_observation(self, observation: str, metrics: Dict[str, Any]):
        """Log performance observations with metrics."""
        self.log_insight(
            category="Performance",
            title="Performance Observation",
            content=observation,
            context=metrics
        )
    
    def log_unexpected_behavior(self, behavior: str, expected: str, actual: str):
        """Log unexpected system behavior."""
        self.log_insight(
            category="Unexpected Behavior",
            title="Behavior Anomaly",
            content=f"**Expected**: {expected}\n**Actual**: {actual}\n**Analysis**: {behavior}"
        )
    
    def log_optimization_opportunity(self, opportunity: str, potential_impact: str):
        """Log optimization opportunities discovered."""
        self.log_insight(
            category="Optimization",
            title="Optimization Opportunity",
            content=f"**Opportunity**: {opportunity}\n**Potential Impact**: {potential_impact}"
        )

# Convenience functions for easy integration
def create_event_logger(experiment_name: str) -> EventLogger:
    """Factory function to create a configured event logger."""
    return EventLogger(run_id=f"{experiment_name}_{datetime.now():%Y%m%d_%H%M%S}")

def create_insight_logger(experiment_name: str) -> AgentInsightLogger:
    """Factory function to create an agent insight logger."""
    return AgentInsightLogger(experiment_name)