"""
Enhanced Trace Handler with Complete Provenance Capture
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

# Import core components - use relative imports within crystalyse.provenance
from ..core import JSONLLogger, MaterialsTracker, MCPDetector
from ..core.pydantic_serializer import create_enhanced_material_record, serialize_pydantic_model
from ..value_registry import get_global_registry


import re as _re

# Scientific keywords that are worth capturing when the agent mentions them
_SCIENTIFIC_KEYWORDS = [
    # Models / force fields
    "MACE-MP", "MACE-OFF", "MACE", "CHGNet", "M3GNet", "SevenNet",
    # Optimisers
    "BFGS", "L-BFGS", "LBFGS", "FIRE",
    # EOS types
    "Birch-Murnaghan", "BirchMurnaghan", "Murnaghan", "Vinet",
    # Symmetry / structure labels
    "Fm-3m", "Pm-3m", "P63/mmc", "R-3c", "Pnma", "P21/c", "Fd-3m",
    # Methods
    "DFT", "GGA", "PBE", "MP-compatible",
]
# Build a single case-sensitive regex that matches any of them as whole tokens
_KW_PATTERN = _re.compile(
    r"(?<![A-Za-z0-9/-])(" + "|".join(_re.escape(k) for k in _SCIENTIFIC_KEYWORDS) + r")(?![A-Za-z0-9/-])"
)
# Regex to find numbers, optionally with sign/exponent, followed by optional unit
_NUM_PATTERN = _re.compile(
    r"([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)"  # number
    r"(?:\s*([eVÅGPaJ/atoms\w°]+))?",      # optional unit
    _re.UNICODE,
)
_CONTEXT_WINDOW = 40  # chars on each side of the number to include as context


def _extract_response_values(text: str) -> dict:
    """
    Scan assistant response text and return:
      - numbers: list of {value, unit, context} for every number mentioned
      - keywords: list of scientific method/model names mentioned
    """
    numbers = []
    seen_spans: list[tuple[int, int]] = []

    for m in _NUM_PATTERN.finditer(text):
        start, end = m.span()
        # Avoid overlapping matches
        if any(s <= start < e for s, e in seen_spans):
            continue
        seen_spans.append((start, end))

        raw_val = m.group(1)
        unit = (m.group(2) or "").strip()

        # Skip plain integers that are just list indices / markdown (e.g. "1.", "2.")
        if unit in ("", ".") and "." not in raw_val and abs(int(float(raw_val))) < 10:
            continue

        ctx_start = max(0, start - _CONTEXT_WINDOW)
        ctx_end = min(len(text), end + _CONTEXT_WINDOW)
        context = text[ctx_start:ctx_end].replace("\n", " ").strip()

        numbers.append({"value": raw_val, "unit": unit, "context": context})

    keywords = list(dict.fromkeys(m.group(1) for m in _KW_PATTERN.finditer(text)))

    return {"numbers": numbers, "keywords": keywords}


# Base class for trace handling (using duck typing to avoid circular import)
class ToolTraceHandler:
    """Minimal base class for trace handling (duck typing interface)."""

    def __init__(self, console: Console):
        self.console = console

    def on_event(self, event):
        """Handle trace event."""
        pass


try:
    from agents.items import ItemHelpers
except ImportError:

    class ItemHelpers:
        @staticmethod
        def text_message_output(item):
            if hasattr(item, "content"):
                return item.content
            return ""


logger = logging.getLogger(__name__)


@dataclass
class EnhancedToolCall:
    """Enhanced tool call tracking with MCP detection."""

    call_id: str
    wrapper_name: str  # SDK wrapper name (often "unknown_tool")
    mcp_tool: str | None = None  # Actual MCP tool detected
    args: dict[str, Any] = None
    start_time: float = 0
    end_time: float | None = None
    output: Any | None = None
    materials_extracted: list[Any] = None
    success: bool = True

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0

    @property
    def tool_name(self) -> str:
        """Return MCP tool if detected, otherwise wrapper."""
        return self.mcp_tool or self.wrapper_name


class ProvenanceTraceHandler(ToolTraceHandler):
    """
    Complete provenance trace handler for CrystaLyse.

    Features:
    - Detects actual MCP tool names (not SDK wrappers)
    - Extracts materials with energies
    - Captures complete event stream in JSONL
    - Saves raw tool outputs for debugging
    - Generates comprehensive summaries
    """

    def __init__(
        self,
        console: Console | None = None,
        output_dir: Path | None = None,
        session_id: str | None = None,
        enable_provenance: bool = True,
        enable_visual: bool = True,
        capture_mcp_logs: bool = False,
        save_raw_outputs: bool = True,
    ):
        """
        Initialize provenance handler.

        Args:
            console: Rich console for visual output
            output_dir: Directory for provenance files
            session_id: Unique session identifier
            enable_provenance: Enable provenance capture
            enable_visual: Show visual trace output
            capture_mcp_logs: Attempt to capture MCP server logs
            save_raw_outputs: Save raw tool outputs for debugging
        """
        super().__init__(console or Console())

        self.enable_provenance = enable_provenance
        self.enable_visual = enable_visual
        self.capture_mcp_logs = capture_mcp_logs
        self.save_raw_outputs = save_raw_outputs

        # Session management
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")

        if enable_provenance and output_dir:
            # Set up output directory
            self.output_dir = Path(output_dir) / f"runs/{self.session_id}"
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Initialize loggers
            self.event_logger = JSONLLogger(self.output_dir / "events.jsonl")
            self.materials_logger = JSONLLogger(self.output_dir / "materials.jsonl")

            # Initialize trackers
            self.materials_tracker = MaterialsTracker()
            self.mcp_detector = MCPDetector()

            # State tracking
            self.tool_calls: dict[str, EnhancedToolCall] = {}
            self.tool_counter = 0
            self.run_start_time = time.time()
            self.first_token_time: float | None = None
            self.assistant_buffer: list[str] = []

            # Conversation tracking (user queries, clarifications, responses)
            self.conversation_log: list[dict[str, Any]] = []
            self.user_query: str | None = None
            self.clarification_exchanges: list[dict[str, Any]] = []

            # Log session start
            self.event_logger.log_session_start(
                self.session_id,
                {"output_dir": str(self.output_dir), "capture_mcp_logs": capture_mcp_logs},
            )
            self._finalized = False
        else:
            self.output_dir = None
            self.event_logger = None
            self._finalized = False

    def on_event(self, event):
        """Process SDK events with provenance capture."""
        # Visual display if enabled
        if self.enable_visual:
            super().on_event(event)

        # Provenance capture
        if not self.enable_provenance or not self.event_logger:
            return

        # DEBUG: Log all event types
        logger.debug(f"Event received: type={event.type}, has_item={hasattr(event, 'item')}")
        if hasattr(event, "item"):
            logger.debug(
                f"  Item type: {event.item.type if hasattr(event.item, 'type') else 'no type'}"
            )

        try:
            if event.type == "run_item_stream_event":
                self._process_stream_event(event.item)
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            if self.event_logger:
                self.event_logger.log(
                    "error", {"error": str(e), "event_type": getattr(event, "type", "unknown")}
                )

    def _process_stream_event(self, item):
        """Process different types of stream events."""
        if item.type == "tool_call_item":
            self._on_tool_call_start(item)
        elif item.type == "tool_call_output_item":
            self._on_tool_call_end(item)
        elif item.type == "message_output_item":
            self._on_message_output(item)
        elif item.type == "reasoning_item":
            self._on_reasoning(item)

    def _on_tool_call_start(self, item):
        """Track tool call start."""
        # Extract basic info
        wrapper_name = self._extract_tool_name(item)
        args = self._extract_tool_args(item)
        call_id = self._get_call_id(item)

        # Create tool call tracker
        tool_call = EnhancedToolCall(
            call_id=call_id, wrapper_name=wrapper_name, args=args, start_time=time.time()
        )
        self.tool_calls[call_id] = tool_call

        # Log event — include input args so input numerics (fmax, steps, etc.) are traceable
        self.event_logger.log(
            "tool_start",
            {
                "wrapper": wrapper_name,
                "call_id": call_id,
                "args": args,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def _on_tool_call_end(self, item):
        """Track tool call end with MCP detection and Pydantic serialization."""
        call_id = self._find_matching_call(item)
        if not call_id or call_id not in self.tool_calls:
            return

        tool_call = self.tool_calls[call_id]
        tool_call.end_time = time.time()
        tool_call.output = item.output

        # Serialize Pydantic models if present
        serialized_output = serialize_pydantic_model(item.output)

        # Save raw output if enabled
        if self.save_raw_outputs and self.output_dir and serialized_output:
            self._save_raw_output(call_id, serialized_output)

        # Detect actual MCP tool
        #mcp_tool = self.mcp_detector.detect_tool(serialized_output)
        #if mcp_tool:
            #tool_call.mcp_tool = mcp_tool

        # --- REPLACE WITH THIS NEW BLOCK ---
        # Robust Content-Based Tool Detection
        # This fixes the issue where tools labeled "unknown_tool" are miscategorized.
        import json
        try:
            # Ensure we have a dictionary to inspect
            if isinstance(serialized_output, str):
                # Sometimes the output is double-serialized
                try:
                    output_data = json.loads(serialized_output)
                    if isinstance(output_data, dict) and "text" in output_data:
                         output_data = json.loads(output_data["text"])
                except:
                    output_data = json.loads(serialized_output)
            else:
                output_data = serialized_output

            if isinstance(output_data, dict):
                # 1. Check for Equation of State results (e.g., b0, v0)
                if "eos_type" in output_data or ("b0" in output_data and "v0" in output_data):
                    mcp_tool = "fit_equation_of_state"
                # 2. Check for Structure Relaxation results
                elif "relaxed_structure" in output_data or "final_energy" in output_data:
                    mcp_tool = "relax_structure"
                # 3. Check for Symmetry/Space Group analysis
                elif "space_group_symbol" in output_data:
                    mcp_tool = "analyze_space_group"
                # 4. Check for structure screening results
                elif "ranked_structures" in output_data and "total_screened" in output_data:
                    mcp_tool = "screen_structures"
                else:
                    # Fallback to existing detector if no specific keys are found
                    mcp_tool = self.mcp_detector.detect_tool(serialized_output)
            else:
                mcp_tool = self.mcp_detector.detect_tool(serialized_output)

        except Exception:
            # Safely handle any parsing errors by falling back to the default detector
            mcp_tool = self.mcp_detector.detect_tool(serialized_output)

        if mcp_tool:
            tool_call.mcp_tool = mcp_tool
        # -----------------------------------

        # Extract materials with enhanced tracking
        materials = self.materials_tracker.extract_from_output(
            serialized_output, mcp_tool or tool_call.wrapper_name
        )
        # if materials:
        #     tool_call.materials_extracted = materials
        #     # Log each material with enhanced metadata
        #     for material in materials:
        #         self.materials_logger.log("material", material.to_dict())

        # FIX: Normalize chemical formulas (e.g. CaO3Ti -> CaTiO3)
        # This ensures your database is searchable later.
        if materials:
            try:
                from pymatgen.core import Composition
                for mat in materials:
                    # Check if formula exists and needs standardization
                    if hasattr(mat, "formula") and mat.formula:
                        try:
                            # 'reduced_formula' automatically sorts elements (Ca-Ti-O)
                            clean_formula = Composition(mat.formula).reduced_formula
                            mat.formula = clean_formula
                        except Exception:
                            pass # If it's not a valid formula, leave it alone
            except ImportError:
                pass # If pymatgen is missing, skip this step

            tool_call.materials_extracted = materials
            
            # Log each material with the now-standardized formula
            for material in materials:
                self.materials_logger.log("material", material.to_dict())


        # Register with value registry for render gate
        registry = get_global_registry()
        if registry and mcp_tool:
            registry.register_tool_output(
                tool_name=mcp_tool,
                tool_call_id=call_id,
                input_data={},  # Could extract from tool_call.args if needed
                output_data=serialized_output,
                timestamp=datetime.now().isoformat(),
            )

        # Create enhanced material record for Phase 1.5 tools
        if mcp_tool and mcp_tool.startswith(
            ("validate_", "calculate_", "analyze_", "predict_", "generate_", "relax_", "fit_")
        ):
            enhanced_record = create_enhanced_material_record(
                mcp_tool, serialized_output, datetime.now().isoformat()
            )
            self.event_logger.log("enhanced_material", enhanced_record)

        # Log tool end with serialized data
        self.event_logger.log(
            "tool_end",
            {
                "wrapper": tool_call.wrapper_name,
                "mcp_tool": tool_call.mcp_tool,
                "duration_ms": tool_call.duration_ms,
                "materials_count": len(materials),
                "call_id": call_id,
                "has_pydantic": hasattr(item.output, "model_dump") or hasattr(item.output, "dict"),
                "timestamp": datetime.now().isoformat(),
            },
        )

    def _on_message_output(self, item):
        """Capture assistant message output."""
        # Track first token time
        if not self.first_token_time:
            self.first_token_time = time.time()
            ttfb = (self.first_token_time - self.run_start_time) * 1000
            self.event_logger.log(
                "ttfb", {"time_ms": ttfb, "timestamp": datetime.now().isoformat()}
            )

        # Extract text
        try:
            text = ItemHelpers.text_message_output(item)
            if text:
                self.assistant_buffer.append(text)
                # Log every number and scientific keyword mentioned in this response chunk
                try:
                    values = _extract_response_values(text)
                    if self.event_logger and (values["numbers"] or values["keywords"]):
                        self.event_logger.log(
                            "response_values",
                            {
                                "numbers": values["numbers"],
                                "keywords": values["keywords"],
                                "timestamp": datetime.now().isoformat(),
                            },
                        )
                except Exception:
                    pass
        except Exception:
            pass

    def _on_reasoning(self, item):
        """Track reasoning tokens."""
        if hasattr(item, "content") and item.content:
            self.event_logger.log(
                "reasoning", {"length": len(item.content), "timestamp": datetime.now().isoformat()}
            )

    #def _extract_tool_name(self, item) -> str:
        #"""Extract tool name from item."""
        #try:
            #if hasattr(item.raw_item, "function"):
                #func = item.raw_item.function
                #if hasattr(func, "name"):
                    #return func.name
        #except Exception:
            #pass
        #return "unknown_tool"

    def _extract_tool_name(self, item) -> str:
        """Extract tool name from item robustly."""
        # 1. Try direct attribute on the item wrapper
        if hasattr(item, "name") and item.name:
            return item.name
            
        # 2. Try function name on the item wrapper (Common in Agent SDKs)
        if hasattr(item, "function") and hasattr(item.function, "name"):
            return item.function.name
            
        # 3. Try raw_item (The underlying OpenAI SDK object)
        if hasattr(item, "raw_item"):
            raw = item.raw_item
            if hasattr(raw, "function") and hasattr(raw.function, "name"):
                return raw.function.name
            if hasattr(raw, "name"):  # Sometimes name is at the top level
                return raw.name
                
        # 4. Try parsing from dictionary dump (Last resort)
        try:
            if hasattr(item, "model_dump"):
                data = item.model_dump()
                if "function" in data and "name" in data["function"]:
                    return data["function"]["name"]
        except Exception:
            pass

        return "unknown_tool"


    def _extract_tool_args(self, item) -> dict:
        """Extract tool arguments."""
        try:
            if hasattr(item.raw_item, "function"):
                func = item.raw_item.function
                if hasattr(func, "arguments"):
                    if isinstance(func.arguments, str):
                        return json.loads(func.arguments)
                    return func.arguments
        except Exception:
            pass
        return {}

    def _get_call_id(self, item) -> str:
        """Get or generate call ID."""
        if hasattr(item.raw_item, "id"):
            return item.raw_item.id
        elif hasattr(item, "id"):
            return item.id
        else:
            self.tool_counter += 1
            return f"call_{self.tool_counter}"

    def _find_matching_call(self, item) -> str | None:
        """Find matching tool call for output."""
        # Try to get ID from item
        if hasattr(item.raw_item, "tool_call_id"):
            return item.raw_item.tool_call_id
        elif hasattr(item, "tool_call_id"):
            return item.tool_call_id

        # Find most recent uncompleted call
        for call_id, tc in reversed(list(self.tool_calls.items())):
            if tc.end_time is None:
                return call_id

        return None

    def _save_raw_output(self, call_id: str, output: Any):
        """Save raw tool output for debugging."""
        try:
            raw_file = self.output_dir / f"raw_output_{call_id[:8]}.json"

            if isinstance(output, str):
                with open(raw_file, "w") as f:
                    f.write(output)
            else:
                with open(raw_file, "w") as f:
                    json.dump(output, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save raw output: {e}")

    def set_user_query(self, query: str):
        """
        Record the user's original query.

        Args:
            query: The user's original query text
        """
        if not self.enable_provenance:
            return

        # Avoid duplicate entries if query already set
        if self.user_query is not None:
            return

        self.user_query = query
        self.conversation_log.append(
            {
                "role": "user",
                "content": query,
                "timestamp": datetime.now().isoformat(),
                "type": "query",
            }
        )

        if self.event_logger:
            self.event_logger.log(
                "user_query", {"query": query, "timestamp": datetime.now().isoformat()}
            )

    def add_clarification_exchange(
        self,
        question: str,
        answer: str,
        question_id: str | None = None,
        options: list[str] | None = None,
    ):
        """
        Record a clarification question and answer.

        Args:
            question: The clarification question asked
            answer: The user's response
            question_id: Optional identifier for the question
            options: Optional list of options presented to user
        """
        if not self.enable_provenance:
            return

        exchange = {
            "question": question,
            "answer": answer,
            "question_id": question_id,
            "options": options,
            "timestamp": datetime.now().isoformat(),
        }
        self.clarification_exchanges.append(exchange)

        # Add to conversation log
        self.conversation_log.append(
            {
                "role": "assistant",
                "content": question,
                "timestamp": datetime.now().isoformat(),
                "type": "clarification_question",
                "options": options,
            }
        )
        self.conversation_log.append(
            {
                "role": "user",
                "content": answer,
                "timestamp": datetime.now().isoformat(),
                "type": "clarification_answer",
                "question_id": question_id,
            }
        )

        if self.event_logger:
            self.event_logger.log("clarification", exchange)

    def add_enriched_query(self, enriched_query: str):
        """
        Record the enriched/processed query sent to the agent.

        Args:
            enriched_query: The processed query with context
        """
        if not self.enable_provenance:
            return

        self.conversation_log.append(
            {
                "role": "system",
                "content": enriched_query,
                "timestamp": datetime.now().isoformat(),
                "type": "enriched_query",
            }
        )

        if self.event_logger:
            self.event_logger.log(
                "enriched_query", {"query": enriched_query, "timestamp": datetime.now().isoformat()}
            )

    def _save_conversation_log(self):
        """Save the complete conversation as a formatted markdown file."""
        if not self.conversation_log and not self.user_query:
            return

        conv_file = self.output_dir / "conversation_full.md"

        lines = [
            "# Crystalyse Conversation Log",
            "",
            f"**Session ID:** {self.session_id}",
            f"**Timestamp:** {datetime.now().isoformat()}",
            "",
            "---",
            "",
        ]

        for entry in self.conversation_log:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            entry_type = entry.get("type", "message")
            entry.get("timestamp", "")

            if entry_type == "query":
                lines.append("## User Query")
                lines.append("")
                lines.append(f"> {content}")
                lines.append("")
            elif entry_type == "clarification_question":
                lines.append("### Clarification Question")
                lines.append("")
                lines.append(f"**Crystalyse:** {content}")
                options = entry.get("options")
                if options:
                    lines.append("")
                    lines.append(f"*Options: {', '.join(options)}*")
                lines.append("")
            elif entry_type == "clarification_answer":
                lines.append(f"**User:** {content}")
                lines.append("")
            elif entry_type == "enriched_query":
                lines.append("### Processed Query (sent to agent)")
                lines.append("")
                lines.append("```")
                lines.append(content)
                lines.append("```")
                lines.append("")
            elif entry_type == "response":
                lines.append("## Crystalyse Response")
                lines.append("")
                lines.append(content)
                lines.append("")
            else:
                # Generic message
                if role == "user":
                    lines.append(f"**User:** {content}")
                elif role == "assistant":
                    lines.append(f"**Crystalyse:** {content}")
                else:
                    lines.append(f"**{role}:** {content}")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*End of conversation log*")

        with open(conv_file, "w") as f:
            f.write("\n".join(lines))

    # def finalize(self) -> dict[str, Any]:
    #     """Generate final summary and save outputs."""
    #     if not self.enable_provenance or not self.event_logger:
    #         return {}

    #     # Save assistant response (legacy file for backwards compatibility)
    #     full_response = ""
    #     if self.assistant_buffer:
    #         full_response = "".join(self.assistant_buffer)
    #         response_file = self.output_dir / "assistant_full.md"
    #         with open(response_file, "w") as f:
    #             f.write(full_response)

    #         self.event_logger.log(
    #             "assistant_output",
    #             {
    #                 "length": len(full_response),
    #                 "timestamp": datetime.now().isoformat(),
    #                 "session_id": self.session_id,
    #             },
    #         )

    #     # Add assistant response to conversation log (avoid duplicates)
    #     if full_response:
    #         # Check if response already exists in conversation log
    #         has_response = any(
    #             entry.get("type") == "response" and entry.get("role") == "assistant"
    #             for entry in self.conversation_log
    #         )
    #         if not has_response:
    #             self.conversation_log.append(
    #                 {
    #                     "role": "assistant",
    #                     "content": full_response,
    #                     "timestamp": datetime.now().isoformat(),
    #                     "type": "response",
    #                 }
    #             )

    #     # Save complete conversation log as markdown
    #     self._save_conversation_log()

    #     # Save conversation log as JSON for programmatic access
    #     if self.conversation_log:
    #         conv_json_file = self.output_dir / "conversation.json"
    #         with open(conv_json_file, "w") as f:
    #             json.dump(self.conversation_log, f, indent=2)

    #     # Save materials catalog with enhanced metadata
    #     self.materials_tracker.save_catalog(
    #         self.output_dir / "materials_catalog.json", enhanced=True
    #     )

    #     # Generate summary
    #     materials_summary = self.materials_tracker.get_summary()

    #     # Tool statistics
    #     mcp_tools = {}
    #     for tc in self.tool_calls.values():
    #         tool_name = tc.mcp_tool or tc.wrapper_name
    #         if tool_name not in mcp_tools:
    #             mcp_tools[tool_name] = {"count": 0, "total_ms": 0, "materials": 0}
    #         mcp_tools[tool_name]["count"] += 1
    #         mcp_tools[tool_name]["total_ms"] += tc.duration_ms
    #         if tc.materials_extracted:
    #             mcp_tools[tool_name]["materials"] += len(tc.materials_extracted)

    #     # Calculate averages
    #     for tool_stats in mcp_tools.values():
    #         if tool_stats["count"] > 0:
    #             tool_stats["avg_ms"] = tool_stats["total_ms"] / tool_stats["count"]

    #     summary = {
    #         "session_id": self.session_id,
    #         "total_time_s": time.time() - self.run_start_time,
    #         "ttfb_ms": (self.first_token_time - self.run_start_time) * 1000
    #         if self.first_token_time
    #         else None,
    #         "tool_calls_total": len(self.tool_calls),
    #         "materials_found": materials_summary["total_materials"],
    #         "unique_compositions": materials_summary["unique_compositions"],
    #         "mcp_operations": sum(1 for tc in self.tool_calls.values() if tc.mcp_tool),
    #         "timestamp": datetime.now().isoformat(),
    #         "mcp_tools": mcp_tools,
    #         "materials_summary": {
    #             "total": materials_summary["total_materials"],
    #             "with_energy": materials_summary["materials_with_energy"],
    #             "min_energy": materials_summary.get("min_energy"),
    #             "max_energy": materials_summary.get("max_energy"),
    #             "avg_energy": materials_summary.get("avg_energy"),
    #         },
    #     }

    #     # Save summary
    #     with open(self.output_dir / "summary.json", "w") as f:
    #         json.dump(summary, f, indent=2)

    #     # Log session end
    #     self.event_logger.log_session_end(self.session_id, summary)

    #     return summary

    def finalize(self) -> dict[str, Any]:
        """Generate final summary and save outputs (Runs only once)."""
        # FIX: Check if already finalized to prevent duplicate events
        if getattr(self, "_finalized", False):
            return {}

        if not self.enable_provenance or not self.event_logger:
            return {}

        # Mark as finalized immediately
        self._finalized = True

        # Save assistant response (legacy file for backwards compatibility)
        full_response = ""
        if self.assistant_buffer:
            full_response = "".join(self.assistant_buffer)
            if self.output_dir:
                try:
                    response_file = self.output_dir / "assistant_full.md"
                    with open(response_file, "w") as f:
                        f.write(full_response)
                except Exception as e:
                    logger.warning(f"Failed to save assistant output: {e}")

            self.event_logger.log(
                "assistant_output",
                {
                    "length": len(full_response),
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.session_id,
                },
            )

        # Add assistant response to conversation log (avoid duplicates)
        if full_response:
            # Check if response already exists in conversation log
            has_response = any(
                entry.get("type") == "response" and entry.get("role") == "assistant"
                for entry in self.conversation_log
            )
            if not has_response:
                self.conversation_log.append(
                    {
                        "role": "assistant",
                        "content": full_response,
                        "timestamp": datetime.now().isoformat(),
                        "type": "response",
                    }
                )

        # Save complete conversation log as markdown
        if self.output_dir:
            self._save_conversation_log()

            # Save conversation log as JSON for programmatic access
            if self.conversation_log:
                try:
                    conv_json_file = self.output_dir / "conversation.json"
                    with open(conv_json_file, "w") as f:
                        json.dump(self.conversation_log, f, indent=2)
                except Exception:
                    pass

            # Save materials catalog with enhanced metadata
            self.materials_tracker.save_catalog(
                self.output_dir / "materials_catalog.json", enhanced=True
            )

        # Generate summary
        materials_summary = self.materials_tracker.get_summary()

        # Tool statistics
        mcp_tools = {}
        for tc in self.tool_calls.values():
            tool_name = tc.mcp_tool or tc.wrapper_name
            if tool_name not in mcp_tools:
                mcp_tools[tool_name] = {"count": 0, "total_ms": 0, "materials": 0}
            mcp_tools[tool_name]["count"] += 1
            mcp_tools[tool_name]["total_ms"] += tc.duration_ms
            if tc.materials_extracted:
                mcp_tools[tool_name]["materials"] += len(tc.materials_extracted)

        # Calculate averages
        for tool_stats in mcp_tools.values():
            if tool_stats["count"] > 0:
                tool_stats["avg_ms"] = tool_stats["total_ms"] / tool_stats["count"]

        summary = {
            "session_id": self.session_id,
            "total_time_s": time.time() - self.run_start_time,
            "ttfb_ms": (self.first_token_time - self.run_start_time) * 1000
            if self.first_token_time
            else None,
            "tool_calls_total": len(self.tool_calls),
            "materials_found": materials_summary["total_materials"],
            "unique_compositions": materials_summary["unique_compositions"],
            "mcp_operations": sum(1 for tc in self.tool_calls.values() if tc.mcp_tool),
            "timestamp": datetime.now().isoformat(),
            "mcp_tools": mcp_tools,
            "materials_summary": {
                "total": materials_summary["total_materials"],
                "with_energy": materials_summary["materials_with_energy"],
                "min_energy": materials_summary.get("min_energy"),
                "max_energy": materials_summary.get("max_energy"),
                "avg_energy": materials_summary.get("avg_energy"),
            },
        }

        # Save summary
        if self.output_dir:
            with open(self.output_dir / "summary.json", "w") as f:
                json.dump(summary, f, indent=2)

        # Log session end
        self.event_logger.log_session_end(self.session_id, summary)

        return summary