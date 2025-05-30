"""Basic tests for CrystaLyse functionality."""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch

from crystalyse import CrystaLyseAgent
from crystalyse.models import ValidationStatus, MaterialCandidate
from crystalyse.utils import (
    classify_composition,
    analyze_application_requirements,
    select_element_space,
)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_classify_composition(self):
        """Test composition classification."""
        assert classify_composition("LiFePO4") == "oxide"
        assert classify_composition("ZnS") == "sulfide"
        assert classify_composition("GaN") == "nitride"
        assert classify_composition("NaCl") == "chloride"
        assert classify_composition("FeCo") == "intermetallic"
        
    def test_analyze_application_requirements(self):
        """Test application requirement analysis."""
        # Battery application
        req = analyze_application_requirements("Design a cathode for Na-ion battery")
        assert req["application_type"] == "energy_storage"
        assert "Na" in req["preferred_elements"]
        assert "Li" in req["avoid_elements"]
        
        # Solar cell application
        req = analyze_application_requirements("Non-toxic semiconductor for solar cells")
        assert req["application_type"] == "photovoltaic"
        assert "Pb" in req["avoid_elements"]
        
    def test_select_element_space(self):
        """Test element space selection."""
        requirements = {
            "application_type": "energy_storage",
            "preferred_elements": ["Na", "Fe"],
            "avoid_elements": ["Co"]
        }
        
        elements = select_element_space(requirements, exclude_elements=["Ni"])
        
        assert "Na" in elements
        assert "Fe" in elements
        assert "Co" not in elements
        assert "Ni" not in elements
        assert "O" in elements  # Should add default elements


class TestCompositionTools:
    """Test composition generation tools."""
    
    @pytest.mark.asyncio
    async def test_generate_compositions(self):
        """Test composition generation."""
        from crystalyse.tools import generate_compositions
        
        result = await generate_compositions(
            elements=["Ba", "Ti", "O"],
            constraints={"structure_type": "perovskite"},
            target_count=5
        )
        
        data = json.loads(result)
        assert "candidates" in data
        assert len(data["candidates"]) <= 5
        assert all("formula" in c for c in data["candidates"])
        
    @pytest.mark.asyncio
    async def test_validate_composition_batch(self):
        """Test batch composition validation."""
        from crystalyse.tools import validate_composition_batch
        
        result = await validate_composition_batch(
            compositions=["BaTiO3", "LiFePO4", "FeCo"],
            context={"application": "general"}
        )
        
        data = json.loads(result)
        assert "BaTiO3" in data
        assert "LiFePO4" in data
        assert "FeCo" in data
        
        # Check intermetallic handling
        assert data["FeCo"]["chemical_family"] == "intermetallic"


class TestStructureTools:
    """Test structure prediction tools."""
    
    @pytest.mark.asyncio
    async def test_predict_structure_types(self):
        """Test structure type prediction."""
        from crystalyse.tools import predict_structure_types
        
        result = await predict_structure_types(
            composition="BaTiO3",
            application="ferroelectric"
        )
        
        data = json.loads(result)
        assert "predicted_structures" in data
        assert len(data["predicted_structures"]) > 0
        
        # Should predict perovskite for BaTiO3
        structures = data["predicted_structures"]
        assert any(s["structure_type"] == "perovskite" for s in structures)
        
    @pytest.mark.asyncio 
    async def test_analyze_structure_stability(self):
        """Test structure stability analysis."""
        from crystalyse.tools import analyze_structure_stability
        
        result = await analyze_structure_stability(
            composition="BaTiO3",
            structure_type="perovskite",
            temperature=300.0
        )
        
        data = json.loads(result)
        assert "stability_analysis" in data
        assert data["structure_type"] == "perovskite"


class TestDesignTools:
    """Test high-level design tools."""
    
    @pytest.mark.asyncio
    async def test_design_material_for_application(self):
        """Test end-to-end material design."""
        from crystalyse.tools import design_material_for_application
        
        result = await design_material_for_application(
            application="cathode material for Na-ion battery",
            constraints={"exclude_elements": ["Co", "Ni"]}
        )
        
        data = json.loads(result)
        assert "top_candidates" in data
        assert "element_space" in data
        assert "requirements" in data
        assert "generation_summary" in data
        
        # Check that constraints were respected
        for candidate in data["top_candidates"]:
            assert "Co" not in candidate["formula"]
            assert "Ni" not in candidate["formula"]


@pytest.mark.asyncio
class TestCrystaLyseAgent:
    """Test main agent functionality."""
    
    @patch('crystalyse.agents.main_agent.MCPServerStdio')
    async def test_agent_initialization(self, mock_mcp):
        """Test agent can be initialized."""
        agent = CrystaLyseAgent(model="gpt-4", temperature=0.7)
        assert agent.agent.name == "CrystaLyse"
        assert agent.agent.model == "gpt-4"
        assert agent.agent.temperature == 0.7
        
    @patch('crystalyse.agents.main_agent.MCPServerStdio')
    @patch('crystalyse.agents.main_agent.Agent.run')
    async def test_analyze_method(self, mock_run, mock_mcp):
        """Test analyze method."""
        # Mock the agent response
        mock_response = Mock()
        mock_response.messages = [
            Mock(content='{"top_candidates": [{"formula": "NaFePO4"}]}')
        ]
        mock_run.return_value = mock_response
        
        agent = CrystaLyseAgent()
        result = await agent.analyze("Design a Na-ion battery cathode")
        
        assert "NaFePO4" in result
        mock_run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])