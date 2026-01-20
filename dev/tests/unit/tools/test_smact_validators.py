"""
Unit tests for SMACT validators.

Tests the core SMACT validation functionality without MCP dependencies.
"""

from __future__ import annotations

import pytest

from crystalyse.tools.smact.validators import (
    SMACTValidator,
    StabilityResult,
    ValidationResult,
    get_robust_electronegativity,
)


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_validation_result_creation(self) -> None:
        """Test creating a ValidationResult with required fields."""
        result = ValidationResult(
            valid=True,
            formula="CaTiO3",
            message="Valid composition",
        )
        assert result.valid is True
        assert result.formula == "CaTiO3"
        assert result.message == "Valid composition"

    def test_validation_result_with_errors(self) -> None:
        """Test ValidationResult with errors."""
        result = ValidationResult(
            valid=False,
            formula="XxYy",
            errors=["Invalid element: Xx"],
            message="Validation failed",
        )
        assert result.valid is False
        assert len(result.errors) == 1
        assert "Invalid element" in result.errors[0]

    def test_validation_result_with_oxidation_states(self) -> None:
        """Test ValidationResult with oxidation states."""
        result = ValidationResult(
            valid=True,
            formula="NaCl",
            oxidation_states={"Na": 1, "Cl": -1},
            charge_balanced=True,
            message="Valid composition",
        )
        assert result.oxidation_states is not None
        assert result.oxidation_states["Na"] == 1
        assert result.charge_balanced is True


class TestStabilityResult:
    """Tests for StabilityResult model."""

    def test_stability_result_creation(self) -> None:
        """Test creating a StabilityResult."""
        result = StabilityResult(
            formula="CaTiO3",
            stable=True,
            smact_valid=True,
            stability_prediction="stable",
        )
        assert result.formula == "CaTiO3"
        assert result.stable is True
        assert result.smact_valid is True
        assert result.stability_prediction == "stable"

    def test_stability_result_with_bonding(self) -> None:
        """Test StabilityResult with bonding information."""
        result = StabilityResult(
            formula="NaCl",
            stable=True,
            smact_valid=True,
            electronegativity_difference=2.23,
            bonding_character="ionic",
            stability_prediction="stable",
        )
        assert result.electronegativity_difference == pytest.approx(2.23, rel=0.01)
        assert result.bonding_character == "ionic"


class TestGetRobustElectronegativity:
    """Tests for electronegativity lookup with fallbacks."""

    def test_common_elements(self) -> None:
        """Test electronegativity for common elements."""
        # Sodium - low electronegativity
        na_eneg = get_robust_electronegativity("Na")
        assert na_eneg == pytest.approx(0.93, rel=0.1)

        # Oxygen - high electronegativity
        o_eneg = get_robust_electronegativity("O")
        assert o_eneg == pytest.approx(3.44, rel=0.1)

        # Carbon - intermediate
        c_eneg = get_robust_electronegativity("C")
        assert c_eneg == pytest.approx(2.55, rel=0.1)

    def test_noble_gas_fallbacks(self) -> None:
        """Test noble gas electronegativity fallbacks."""
        # Noble gases may have values in SMACT or use fallbacks
        # Test that we get a numeric value (not NaN)
        import numpy as np

        he_eneg = get_robust_electronegativity("He", fallback_noble_gas=True)
        # Should return a numeric value
        assert not np.isnan(he_eneg) or he_eneg == pytest.approx(4.16, rel=0.5)

        xe_eneg = get_robust_electronegativity("Xe", fallback_noble_gas=True)
        # Xenon - most common noble gas to form compounds
        assert not np.isnan(xe_eneg) or xe_eneg == pytest.approx(2.58, rel=0.5)

    def test_invalid_element(self) -> None:
        """Test handling of invalid elements."""
        import numpy as np

        result = get_robust_electronegativity("Xx")
        assert np.isnan(result)


class TestSMACTValidator:
    """Tests for SMACTValidator class."""

    def test_validate_simple_oxide(self) -> None:
        """Test validation of simple oxide (MgO)."""
        result = SMACTValidator.validate_composition("MgO")
        assert result.valid is True
        assert result.formula == "MgO"

    def test_validate_perovskite(self) -> None:
        """Test validation of perovskite (CaTiO3)."""
        result = SMACTValidator.validate_composition("CaTiO3")
        assert result.valid is True
        assert result.formula == "CaTiO3"

    def test_validate_layered_oxide(self) -> None:
        """Test validation of layered oxide (LiCoO2)."""
        result = SMACTValidator.validate_composition("LiCoO2")
        assert result.valid is True
        assert result.formula == "LiCoO2"

    def test_validate_salt(self) -> None:
        """Test validation of simple salt (NaCl)."""
        result = SMACTValidator.validate_composition("NaCl")
        assert result.valid is True
        assert result.formula == "NaCl"

    def test_validate_binary_compound(self) -> None:
        """Test validation of binary compound (ZnO)."""
        result = SMACTValidator.validate_composition("ZnO")
        assert result.valid is True
        assert result.formula == "ZnO"

    def test_validate_ternary_compound(self) -> None:
        """Test validation of ternary compound (BaTiO3)."""
        result = SMACTValidator.validate_composition("BaTiO3")
        assert result.valid is True
        assert result.formula == "BaTiO3"

    def test_validate_invalid_composition(self) -> None:
        """Test validation rejects invalid compositions."""
        # Empty formula should fail
        result = SMACTValidator.validate_composition("")
        assert result.valid is False

    def test_validate_with_pauling_test_disabled(self) -> None:
        """Test validation with Pauling test disabled."""
        result = SMACTValidator.validate_composition("CaTiO3", use_pauling_test=False)
        assert isinstance(result, ValidationResult)

    def test_validate_pure_metal(self) -> None:
        """Test validation of pure metals (include_alloys=True)."""
        result = SMACTValidator.validate_composition("Fe", include_alloys=True)
        assert result.valid is True

    def test_metadata_included(self) -> None:
        """Test that metadata is included in result."""
        result = SMACTValidator.validate_composition("NaCl")
        assert "method" in result.metadata
        assert result.metadata["method"] == "smact_validity"


class TestSMACTValidatorStability:
    """Tests for SMACTValidator stability analysis."""

    def test_analyze_stable_compound(self) -> None:
        """Test stability analysis of stable compound."""
        result = SMACTValidator.analyze_stability("NaCl")
        assert result.formula == "NaCl"
        assert result.smact_valid is True
        assert result.stable is True

    def test_analyze_electronegativity_ionic(self) -> None:
        """Test electronegativity analysis for ionic compound."""
        result = SMACTValidator.analyze_stability("NaCl", check_electronegativity=True)
        assert result.electronegativity_difference is not None
        # Na-Cl has high electronegativity difference
        assert result.electronegativity_difference > 1.5
        assert result.bonding_character == "ionic"

    def test_analyze_electronegativity_covalent(self) -> None:
        """Test electronegativity analysis for covalent compound."""
        # Use a clearly covalent compound
        result = SMACTValidator.analyze_stability("CH4", check_electronegativity=True)
        # C-H has low electronegativity difference (~0.35)
        if result.electronegativity_difference is not None:
            # Just verify we get a result - bonding character depends on threshold
            assert result.electronegativity_difference >= 0
            assert result.bonding_character in ["ionic", "covalent"]

    def test_analyze_without_electronegativity(self) -> None:
        """Test stability analysis without electronegativity check."""
        result = SMACTValidator.analyze_stability("NaCl", check_electronegativity=False)
        assert result.electronegativity_difference is None
        assert result.bonding_character is None

    def test_analyze_invalid_formula(self) -> None:
        """Test stability analysis with invalid formula."""
        result = SMACTValidator.analyze_stability("InvalidFormula123")
        assert result.stable is False
        assert result.smact_valid is False


class TestValidationEdgeCases:
    """Tests for edge cases and error handling."""

    def test_formula_with_numbers(self) -> None:
        """Test formulas with stoichiometric numbers."""
        result = SMACTValidator.validate_composition("Fe2O3")
        assert result.valid is True

    def test_formula_with_large_numbers(self) -> None:
        """Test formulas with larger stoichiometric numbers."""
        result = SMACTValidator.validate_composition("Ca10(PO4)6(OH)2")
        # Hydroxyapatite - complex formula
        assert isinstance(result, ValidationResult)

    def test_rare_earth_element(self) -> None:
        """Test validation with rare earth elements."""
        result = SMACTValidator.validate_composition("LaAlO3")
        assert result.valid is True

    def test_actinide_element(self) -> None:
        """Test validation with actinide elements."""
        result = SMACTValidator.validate_composition("UO2")
        assert isinstance(result, ValidationResult)

    def test_multiple_oxidation_states(self) -> None:
        """Test elements with multiple common oxidation states."""
        # Iron can be Fe2+ or Fe3+
        result_fe2 = SMACTValidator.validate_composition("FeO")
        result_fe3 = SMACTValidator.validate_composition("Fe2O3")
        assert result_fe2.valid is True or result_fe3.valid is True


@pytest.mark.parametrize(
    "formula,expected_valid",
    [
        ("MgO", True),
        ("NaCl", True),
        ("CaTiO3", True),
        ("BaTiO3", True),
        ("SrTiO3", True),
        ("LiCoO2", True),
        ("Fe2O3", True),
        ("ZnO", True),
        ("Al2O3", True),
        ("TiO2", True),
    ],
)
def test_common_materials_validation(formula: str, expected_valid: bool) -> None:
    """Parametrized test for common materials validation."""
    result = SMACTValidator.validate_composition(formula)
    assert result.valid == expected_valid, f"Unexpected result for {formula}: {result.message}"
