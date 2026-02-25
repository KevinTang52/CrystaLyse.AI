"""
Pydantic model serialization for Phase 1.5 provenance capture.

Handles serialization of Pydantic models from CrystaLyse tools to
ensure rich data capture in provenance system.
"""
try:
    from pymatgen.core import Composition
except ImportError:
    Composition = None

# Add this at the top with other imports
from .mcp_detector import MCPDetector

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def serialize_pydantic_model(obj: Any) -> dict | list | str | int | float | bool | None:
    """
    Serialize a Pydantic model or any Python object to JSON-compatible format.

    Handles:
    - Pydantic v2 models (model_dump)
    - Pydantic v1 models (dict)
    - Dataclasses
    - Datetime objects
    - Path objects
    - Lists, dicts, and primitives

    Args:
        obj: Object to serialize

    Returns:
        JSON-serializable representation
    """
    # Handle None
    if obj is None:
        return None

    # Handle primitives
    if isinstance(obj, str | int | float | bool):
        return obj

    # Handle datetime
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Handle Path
    if isinstance(obj, Path):
        return str(obj)

    # Handle Pydantic v2 models
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump(exclude_none=True, mode="json")
        except Exception as e:
            logger.debug(f"model_dump failed: {e}, trying fallback")
            try:
                return obj.model_dump()
            except Exception:
                pass

    # Handle Pydantic v1 models
    if hasattr(obj, "dict"):
        try:
            return obj.dict(exclude_none=True)
        except Exception as e:
            logger.debug(f"dict() failed: {e}, trying without exclude_none")
            try:
                return obj.dict()
            except Exception:
                pass

    # Handle dataclasses
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict

        try:
            return asdict(obj)
        except Exception:
            pass

    # Handle lists/tuples
    if isinstance(obj, list | tuple):
        return [serialize_pydantic_model(item) for item in obj]

    # Handle dicts
    if isinstance(obj, dict):
        return {key: serialize_pydantic_model(value) for key, value in obj.items()}

    # Handle objects with __dict__
    if hasattr(obj, "__dict__"):
        return {
            key: serialize_pydantic_model(value)
            for key, value in obj.__dict__.items()
            if not key.startswith("_")
        }

    # Fallback to string representation
    return str(obj)


def extract_pydantic_fields(data: dict[str, Any]) -> dict[str, Any]:
    """
    Extract and flatten key fields from Pydantic model outputs.

    This function identifies common patterns in Phase 1.5 tool outputs
    and extracts the most important fields for materials tracking.

    Args:
        data: Serialized Pydantic model data

    Returns:
        Dictionary with extracted key fields
    """
    extracted = {}

    # Common fields to extract at top level
    top_level_fields = [
        "formula",
        "composition",
        "success",
        "is_valid",
        "is_stable",
        "formation_energy",
        "energy_above_hull",
        "band_gap",
        "space_group",
        "bulk_modulus",
        "stress_tensor",
        "confidence",
        "checkpoint_used",
        "method",
        "error",
    ]

    for field in top_level_fields:
        if field in data:
            extracted[field] = data[field]

    # Extract nested structure data
    if "predicted_structures" in data and isinstance(data["predicted_structures"], list):
        extracted["num_structures"] = len(data["predicted_structures"])
        # Extract first structure details if available
        if data["predicted_structures"]:
            first = data["predicted_structures"][0]
            if isinstance(first, dict):
                extracted["first_structure"] = {
                    "formula": first.get("formula"),
                    "volume": first.get("volume"),
                    "confidence": first.get("confidence", 1.0),
                }

    # Extract dopant information
    if "n_type_dopants" in data and "p_type_dopants" in data:
        extracted["dopants"] = {
            "n_type": data["n_type_dopants"][:3] if data["n_type_dopants"] else [],
            "p_type": data["p_type_dopants"][:3] if data["p_type_dopants"] else [],
        }

    # Extract ML representation summary
    if "representation" in data and isinstance(data["representation"], list):
        extracted["ml_vector_length"] = len(data["representation"])
        extracted["ml_vector_nonzero"] = sum(1 for x in data["representation"] if x != 0)

    # Extract stress/mechanical properties
    if "stress_tensor" in data:
        extracted["has_stress_data"] = True
        if "pressure" in data:
            extracted["pressure"] = data["pressure"]
        if "von_mises_stress" in data:
            extracted["von_mises_stress"] = data["von_mises_stress"]

    return extracted


#def create_enhanced_material_record(
    #tool_name: str, tool_output: Any, timestamp: str | None = None
#) -> dict[str, Any]:
    """
    Create an enhanced material record from Phase 1.5 tool output.

    Args:
        tool_name: Name of the tool that generated the output
        tool_output: Raw or Pydantic model output from the tool
        timestamp: Optional timestamp (auto-generated if not provided)

    Returns:
        Enhanced material record with rich metadata
    """
    # Serialize the output
    serialized = serialize_pydantic_model(tool_output)

    # Extract key fields
    if isinstance(serialized, dict):
        key_fields = extract_pydantic_fields(serialized)
    else:
        key_fields = {}

    # Build enhanced record
    record = {
        "tool": tool_name,
        "timestamp": timestamp or datetime.now().isoformat(),
        "key_data": key_fields,
        "full_output": serialized,
    }

    # Add tool category
    from .mcp_detector import MCPDetector

    record["tool_category"] = MCPDetector.get_tool_category(tool_name)

    # Determine if this is a successful result
    if isinstance(serialized, dict):
        # Check various success indicators
        record["successful"] = (
            serialized.get("success", False)
            or serialized.get("is_valid", False)
            or serialized.get("formation_energy") is not None
            or serialized.get("predicted_structures") is not None
        )
    else:
        record["successful"] = False

    return record


def _categorize_tool(tool_name: str) -> str:
    """Categorize tool for metadata."""
    if not tool_name:
        return "unknown"
    
    if tool_name.startswith("validate_"):
        return "validation"
    elif tool_name.startswith("generate_"):
        return "generation"
    elif tool_name.startswith("relax_"):
        return "optimization"
    elif tool_name.startswith("calculate_") or tool_name.startswith("fit_"):
        return "calculation"
    elif tool_name.startswith("analyze_") or tool_name.startswith("predict_"):
        return "analysis"
    return "other"



#def create_enhanced_material_record(tool_name: str, tool_output: Any, timestamp: str | None = None) -> dict[str, Any]:
    """Create a standardized record for material discovery events."""
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    # Serialize first
    serialized = serialize_pydantic_model(tool_output)
    
    # FIX: Unwrap the data to find the actual scientific payload
    # This fixes the bug where "successful: false" was reported for valid tools
    actual_data = MCPDetector._unwrap_output(serialized)

    # Base record structure
    record = {
        "tool": tool_name,
        "timestamp": timestamp,
        "key_data": {},
        "full_output": serialized if isinstance(serialized, str) else json.dumps(serialized),
        "tool_category": _categorize_tool(tool_name),
        "successful": False  # Default to False until proven True
    }

    # Intelligent Success Detection
    if isinstance(actual_data, dict):
        # Check standard success flags and scientific indicators
        record["successful"] = (
            actual_data.get("success", False) or
            actual_data.get("valid", False) or 
            actual_data.get("converged", False) or          # For relaxation
            actual_data.get("is_valid", False) or           # For validation
            actual_data.get("formation_energy") is not None or # For energy
            actual_data.get("b0") is not None or            # For EOS
            actual_data.get("space_group_symbol") is not None # For space group
        )
        
        # Extract key data for easier reading (optional but recommended)
        if "formula" in actual_data:
            record["key_data"]["formula"] = actual_data["formula"]
        if "formation_energy" in actual_data:
            record["key_data"]["energy"] = actual_data["formation_energy"]
            
    return record

def create_enhanced_material_record(tool_name: str, tool_output: Any, timestamp: str | None = None) -> dict[str, Any]:
    """Create a standardized record for material discovery events."""
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    # Serialize first
    serialized = serialize_pydantic_model(tool_output)
    
    # FIX: Unwrap the data to find the actual scientific payload
    # This fixes the bug where "successful: false" was reported for valid tools
    actual_data = MCPDetector._unwrap_output(serialized)

    # Ensure json is available for dumping
    import json

    # Base record structure
    record = {
        "tool": tool_name,
        "timestamp": timestamp,
        "key_data": {},
        "full_output": serialized if isinstance(serialized, str) else json.dumps(serialized),
        "tool_category": _categorize_tool(tool_name),
        "successful": False  # Default to False until proven True
    }

    # Intelligent Success Detection
    if isinstance(actual_data, dict):
        # Check standard success flags and scientific indicators
        record["successful"] = (
            actual_data.get("success", False) or
            actual_data.get("valid", False) or 
            actual_data.get("converged", False) or          # For relaxation
            actual_data.get("is_valid", False) or           # For validation
            actual_data.get("formation_energy") is not None or # For energy
            actual_data.get("b0") is not None or            # For EOS
            actual_data.get("space_group_symbol") is not None # For space group
        )
        
        # # --- NEW NORMALIZATION LOGIC ---
        # # Extract and Normalize Key Scientific Data
        # # We explicitly look for these fields to populate the summary 'key_data'
        # key_fields_to_extract = ["formula", "composition", "formation_energy", "energy", "volume", "b0", "v0"]
        
        # for k in key_fields_to_extract:
        #     if k in actual_data:
        #         # FIX: Normalize chemical formulas immediately (BaO3Zr -> BaZrO3)
        #         if k == "formula" and Composition:
        #             try:
        #                 raw_formula = actual_data[k]
        #                 if raw_formula:
        #                     # Force Hill Notation (standard ordering via pymatgen)
        #                     record["key_data"][k] = Composition(raw_formula).reduced_formula
        #                 else:
        #                     record["key_data"][k] = raw_formula
        #             except Exception:
        #                 record["key_data"][k] = actual_data[k] # Fallback if parsing fails
        #         else:
        #             record["key_data"][k] = actual_data[k]
        # # -------------------------------
        # --- NEW NORMALIZATION LOGIC ---
        # Extract and Normalize Key Scientific Data
        # Updated to catch 'e0' and 'final_energy'
        
        key_fields_to_extract = [
            "formula", "composition", 
            "formation_energy", "energy", "final_energy", "e0",  # Added e0 and final_energy
            "volume", "b0", "v0"
        ]
        
        for k in key_fields_to_extract:
            if k in actual_data:
                # 1. Normalize Chemical Formulas
                if k == "formula" and Composition:
                    try:
                        raw_formula = actual_data[k]
                        if raw_formula:
                            record["key_data"][k] = Composition(raw_formula).reduced_formula
                        else:
                            record["key_data"][k] = raw_formula
                    except Exception:
                        record["key_data"][k] = actual_data[k]
                
                # 2. Normalize Energy (Map 'e0' and 'final_energy' to 'energy')
                elif k in ["e0", "final_energy", "formation_energy"]:
                    record["key_data"]["energy"] = actual_data[k]
                    # Also keep the original key for debugging
                    record["key_data"][k] = actual_data[k]
                    
                # 3. Everything else (b0, v0, etc.)
                else:
                    record["key_data"][k] = actual_data[k]
        # -------------------------------
            
    return record