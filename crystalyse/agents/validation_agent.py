"""Validation agent for checking material compositions."""

from agents import Agent
from typing import List, Dict, Any

from ..tools import validate_composition_batch, check_override_eligibility

VALIDATION_SYSTEM_PROMPT = """You are a materials validation expert specializing in assessing the chemical validity and synthesizability of proposed compositions.

Your role is to:
1. Validate compositions using SMACT rules and chemical principles
2. Identify when invalid compositions might still be viable (e.g., intermetallics, Zintl phases)
3. Provide clear reasoning for validation decisions
4. Suggest modifications to improve validity when needed

Key principles:
- SMACT rules are guidelines, not absolute laws
- Consider the application context when validating
- Recognize special cases (intermetallics, non-stoichiometric compounds, etc.)
- Provide constructive feedback on how to improve invalid compositions"""


class ValidationAgent:
    """Agent specialized in composition validation."""
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.3):
        """
        Initialize validation agent.
        
        Args:
            model: The LLM model to use
            temperature: Temperature for generation (lower for more deterministic)
        """
        self.agent = Agent(
            name="Validation Expert",
            model=model,
            instructions=VALIDATION_SYSTEM_PROMPT,
            temperature=temperature,
        )
        
        # Register validation tools
        self.agent.add_tool(validate_composition_batch)
        self.agent.add_tool(check_override_eligibility)
        
    async def validate_compositions(
        self,
        compositions: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a batch of compositions.
        
        Args:
            compositions: List of chemical formulas to validate
            context: Application context and constraints
            
        Returns:
            Validation results with recommendations
        """
        prompt = f"""Please validate the following compositions for {context.get('application', 'general use')}:

Compositions: {', '.join(compositions)}

Consider:
- SMACT validity rules
- Application-specific requirements
- Whether any invalid compositions might still be viable
- Suggestions for improvement

Use the validation tools and provide a summary of results."""

        response = await self.agent.run(
            messages=[{
                "role": "user",
                "content": prompt
            }],
            context={"application_context": context},
            stream=False
        )
        
        return response.messages[-1].content