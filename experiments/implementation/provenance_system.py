"""
Enhanced provenance system for CrystaLyse experiments.
Tracks computational provenance and prevents hallucination.
"""

import re
import time
import json
import hashlib
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

@dataclass
class ProvenancedValue:
    """A value with complete computational provenance."""
    value: Any
    unit: str
    source_tool: str
    source_artifact_hash: str
    timestamp: datetime = field(default_factory=datetime.now)
    computation_params: Dict[str, Any] = field(default_factory=dict)
    confidence: Optional[float] = None
    value_type: str = "scalar"  # scalar|vector|boolean|string
    tool_version: Optional[str] = None
    
    def to_tuple(self) -> Tuple:
        """Convert to tuple format for placeholders."""
        return (
            self.value, 
            self.unit, 
            self.source_tool,
            self.source_artifact_hash, 
            self.timestamp.isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'value': self.value,
            'unit': self.unit,
            'source_tool': self.source_tool,
            'hash': self.source_artifact_hash,
            'timestamp': self.timestamp.isoformat(),
            'params': self.computation_params,
            'confidence': self.confidence,
            'value_type': self.value_type,
            'tool_version': self.tool_version
        }

class ProvenanceRegistry:
    """Registry for tracking computational provenance."""
    
    def __init__(self):
        self.registry: Dict[str, ProvenancedValue] = {}
        self.lookup_cache: Dict[float, List[str]] = {}
        self._lock = threading.Lock()
    
    def register(self, key: str, pv: ProvenancedValue) -> None:
        """Register a provenanced value."""
        with self._lock:
            self.registry[key] = pv
            
            # Cache numeric values for lookup
            if isinstance(pv.value, (int, float)):
                self.lookup_cache.setdefault(float(pv.value), []).append(key)
            
            logger.debug(f"Registered {key} -> {pv.value} {pv.unit} ({pv.source_tool})")
    
    def has_provenance(self, value: float, tolerance: float = 1e-6) -> bool:
        """Check if a numeric value has provenance."""
        return any(abs(v - value) < tolerance for v in self.lookup_cache.keys())
    
    def get_provenance(self, value: float, tolerance: float = 1e-6) -> Optional[ProvenancedValue]:
        """Get provenance for a numeric value."""
        for v, keys in self.lookup_cache.items():
            if abs(v - value) < tolerance:
                return self.registry[keys[0]]
        return None
    
    def to_json(self, path: Path) -> None:
        """Save registry to JSON file."""
        tmp_path = path.with_suffix('.tmp')
        with open(tmp_path, 'w') as f:
            data = {k: v.to_dict() for k, v in self.registry.items()}
            json.dump(data, f, indent=2, default=str)
        tmp_path.replace(path)
        logger.info(f"Provenance registry saved: {path}")
    
    @classmethod
    def from_json(cls, path: Path) -> "ProvenanceRegistry":
        """Load registry from JSON file."""
        instance = cls()
        if not path.exists():
            return instance
        
        with open(path) as f:
            data = json.load(f)
        
        for k, d in data.items():
            pv = ProvenancedValue(
                value=d["value"],
                unit=d["unit"],
                source_tool=d["source_tool"],
                source_artifact_hash=d["hash"],
                timestamp=datetime.fromisoformat(d["timestamp"]),
                computation_params=d.get("params", {}),
                confidence=d.get("confidence"),
                value_type=d.get("value_type", "scalar"),
                tool_version=d.get("tool_version")
            )
            instance.register(k, pv)
        
        logger.info(f"Loaded {len(instance.registry)} provenance entries")
        return instance
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_values = len(self.registry)
        by_tool = {}
        by_type = {}
        
        for pv in self.registry.values():
            by_tool[pv.source_tool] = by_tool.get(pv.source_tool, 0) + 1
            by_type[pv.value_type] = by_type.get(pv.value_type, 0) + 1
        
        return {
            "total_values": total_values,
            "by_tool": by_tool,
            "by_type": by_type,
            "numeric_cache_size": len(self.lookup_cache)
        }

# Regex patterns for detecting safe numeric contexts
CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
NUMERIC = re.compile(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?")
SAFE_CONTEXTS = [
    re.compile(r"[A-Z][a-z]?\d+"),                       # Chemical formulas: Na3, O2
    re.compile(r"\b(ICSD|MP|AFLOW|COD)-\d+\b"),         # Database IDs
    re.compile(r"\b(Fig(?:ure)?|Table|Section|§)\s*\d+[A-Z]?\b"),  # References
    re.compile(r"\bo\d(?:-mini)?\b"),                    # Model names: o3, o4-mini
    re.compile(r"https?://\S+"),                         # URLs
    re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"),    # Dates
]

def _mask_code_blocks(text: str) -> List[Tuple[int, int]]:
    """Find code block spans to exclude from validation."""
    return [(m.start(), m.end()) for m in CODE_BLOCK.finditer(text)]

def _in_safe_context(text: str, start: int, end: int) -> bool:
    """Check if number appears in a safe context."""
    window = text[max(0, start-20):min(len(text), end+20)]
    return any(pattern.search(window) for pattern in SAFE_CONTEXTS)

def _in_span(pos: int, spans: List[Tuple[int, int]]) -> bool:
    """Check if position is within any span."""
    return any(start <= pos < end for start, end in spans)

class RenderGate:
    """Shadow validation gate for detecting numeric leaks."""
    
    def __init__(self, registry: ProvenanceRegistry, strict: bool = True):
        self.registry = registry
        self.strict = strict
        self.blocked_count = 0
        self.shadow_log: List[Dict[str, Any]] = []
        self.overhead_seconds = 0.0
    
    def check_and_gate(self, text: str) -> str:
        """Check text for unprovenanced numbers and optionally block them."""
        start_time = time.time()
        
        # Find code blocks to skip
        code_spans = _mask_code_blocks(text)
        
        output_parts = []
        last_pos = 0
        
        for match in NUMERIC.finditer(text):
            start, end = match.start(), match.end()
            
            # Add text before this number
            output_parts.append(text[last_pos:start])
            last_pos = end
            
            number_str = match.group()
            
            # Skip if in code block or safe context
            if (_in_span(start, code_spans) or 
                _in_safe_context(text, start, end)):
                output_parts.append(number_str)
                continue
            
            # Check if number has provenance
            try:
                numeric_value = float(number_str)
                has_provenance = self.registry.has_provenance(numeric_value)
            except ValueError:
                # Non-numeric strings that match pattern
                output_parts.append(number_str)
                continue
            
            if has_provenance:
                output_parts.append(number_str)
            else:
                # Log violation
                self.blocked_count += 1
                self.shadow_log.append({
                    "value": number_str,
                    "numeric_value": numeric_value,
                    "position": {"start": start, "end": end},
                    "context": text[max(0, start-50):min(len(text), end+50)],
                    "timestamp": datetime.now().isoformat()
                })
                
                # Block or allow based on strict mode
                if self.strict:
                    output_parts.append("[BLOCKED]")
                else:
                    output_parts.append(number_str)
        
        # Add remaining text
        output_parts.append(text[last_pos:])
        
        self.overhead_seconds += time.time() - start_time
        return "".join(output_parts)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics."""
        return {
            "blocked_count": self.blocked_count,
            "shadow_violations": len(self.shadow_log),
            "overhead_seconds": self.overhead_seconds,
            "would_leak_rate": len(self.shadow_log) / max(1, self.blocked_count + len([v for v in self.shadow_log if "blocked" not in v]))
        }

class PlaceholderRenderer:
    """Production renderer using tuple placeholders."""
    
    def __init__(self, registry: ProvenanceRegistry):
        self.registry = registry
        self.placeholder_pattern = re.compile(r"<<T:([A-Za-z0-9._:-]+)>>")
    
    def render(self, text: str) -> str:
        """Render placeholders with actual values."""
        def replace_placeholder(match):
            key = match.group(1)
            if key not in self.registry.registry:
                raise ValueError(f"Missing tuple key: {key}")
            return str(self.registry.registry[key].value)
        
        return self.placeholder_pattern.sub(replace_placeholder, text)

class CrystaLyseProvenanceWrapper:
    """Wrapper for CrystaLyse agent with provenance tracking."""
    
    def __init__(self, agent, experiment_name: str):
        self.agent = agent
        self.experiment_name = experiment_name
        self.registry = ProvenanceRegistry()
        self.render_gate = RenderGate(self.registry, strict=False)  # Shadow mode
        self.strict_gate = RenderGate(self.registry, strict=True)   # Blocking mode
        
        # Setup logging
        self.provenance_log_dir = Path("experiments/raw_data/provenance_logs")
        self.provenance_log_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_with_provenance(
        self, 
        query: str, 
        mode: str = "adaptive",
        strict_validation: bool = False
    ) -> Dict[str, Any]:
        """Process query with complete provenance tracking."""
        
        # Get original response
        original_result = await self.agent.discover(query)
        response_text = original_result.get("response", "")
        
        # Apply validation gate
        gate = self.strict_gate if strict_validation else self.render_gate
        processed_text = gate.check_and_gate(response_text)
        
        # Save provenance data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        provenance_file = self.provenance_log_dir / f"provenance_{self.experiment_name}_{timestamp}.json"
        self.registry.to_json(provenance_file)
        
        # Log shadow violations
        if gate.shadow_log:
            violations_file = self.provenance_log_dir / f"violations_{self.experiment_name}_{timestamp}.json"
            with open(violations_file, 'w') as f:
                json.dump(gate.shadow_log, f, indent=2)
        
        return {
            **original_result,
            "response": processed_text,
            "provenance_stats": self.registry.get_statistics(),
            "validation_stats": gate.get_statistics(),
            "strict_validation": strict_validation
        }
    
    def register_tool_result(
        self, 
        tool_name: str, 
        operation: str,
        result: Dict[str, Any],
        formula: Optional[str] = None
    ) -> None:
        """Register tool results in provenance system."""
        artifact_hash = self._compute_artifact_hash(result, formula)
        
        # Register different types of results
        if tool_name.lower() == "smact":
            self._register_smact_result(result, artifact_hash, formula)
        elif tool_name.lower() == "chemeleon":
            self._register_chemeleon_result(result, artifact_hash, formula)
        elif tool_name.lower() == "mace":
            self._register_mace_result(result, artifact_hash, formula)
    
    def _compute_artifact_hash(
        self, 
        result: Dict[str, Any], 
        formula: Optional[str] = None
    ) -> str:
        """Compute deterministic hash for computational artifact."""
        # Use formula + result structure for hash
        hash_input = f"{formula or 'unknown'}_{json.dumps(result, sort_keys=True)}"
        return "sha256:" + hashlib.sha256(hash_input.encode()).hexdigest()
    
    def _register_smact_result(
        self, 
        result: Dict[str, Any], 
        artifact_hash: str, 
        formula: Optional[str]
    ) -> None:
        """Register SMACT validation results."""
        if "valid" in result and isinstance(result["valid"], bool):
            self.registry.register(
                f"smact_valid_{formula or 'unknown'}",
                ProvenancedValue(
                    value=1.0 if result["valid"] else 0.0,
                    unit="",  # Dimensionless boolean
                    source_tool="SMACT",
                    source_artifact_hash=artifact_hash,
                    computation_params={"formula": formula},
                    value_type="boolean"
                )
            )
    
    def _register_chemeleon_result(
        self, 
        result: Dict[str, Any], 
        artifact_hash: str, 
        formula: Optional[str]
    ) -> None:
        """Register Chemeleon structure generation results."""
        if "lattice_parameters" in result:
            params = result["lattice_parameters"]
            for param in ["a", "b", "c"]:
                if param in params:
                    self.registry.register(
                        f"chemeleon_lattice_{param}_{formula or 'unknown'}",
                        ProvenancedValue(
                            value=float(params[param]),
                            unit="Angstrom",
                            source_tool="Chemeleon",
                            source_artifact_hash=artifact_hash,
                            computation_params={"formula": formula, "parameter": param},
                            value_type="scalar"
                        )
                    )
    
    def _register_mace_result(
        self, 
        result: Dict[str, Any], 
        artifact_hash: str, 
        formula: Optional[str]
    ) -> None:
        """Register MACE energy calculation results."""
        if "energy_per_atom" in result:
            self.registry.register(
                f"mace_energy_per_atom_{formula or 'unknown'}",
                ProvenancedValue(
                    value=float(result["energy_per_atom"]),
                    unit="eV/atom",
                    source_tool="MACE",
                    source_artifact_hash=artifact_hash,
                    computation_params={"formula": formula},
                    confidence=result.get("uncertainty"),
                    value_type="scalar"
                )
            )
        
        if "total_energy" in result:
            self.registry.register(
                f"mace_total_energy_{formula or 'unknown'}",
                ProvenancedValue(
                    value=float(result["total_energy"]),
                    unit="eV",
                    source_tool="MACE",
                    source_artifact_hash=artifact_hash,
                    computation_params={"formula": formula},
                    value_type="scalar"
                )
            )