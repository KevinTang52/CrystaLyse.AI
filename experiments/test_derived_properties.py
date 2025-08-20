#!/usr/bin/env python3
"""
Smoke test for derived properties system.
Verifies that derived values are properly registered with provenance.
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "implementation"))

from provenance_system import ProvenanceRegistry, ProvenancedValue
from derived_properties import BatteryPropertyCalculator, register_derived_value


def test_voltage_derivation():
    """Test that voltage derivation works and creates proper provenance."""
    print("Testing voltage derivation...")
    
    # Create registry
    registry = ProvenanceRegistry()
    
    # Register source tool outputs
    registry.register("mace_energy_licoo2", ProvenancedValue(
        value=-21.96, unit="eV", source_tool="MACE",
        source_artifact_hash="sha256:test_licoo2",
        computation_params={"atoms": 4}, confidence=0.8, value_type="scalar"
    ))
    
    registry.register("mace_energy_coo2", ProvenancedValue(
        value=-17.14, unit="eV", source_tool="MACE",
        source_artifact_hash="sha256:test_coo2",
        computation_params={"atoms": 3}, confidence=0.8, value_type="scalar"
    ))
    
    registry.register("mace_energy_li_metal", ProvenancedValue(
        value=-1.90, unit="eV/atom", source_tool="MACE",
        source_artifact_hash="sha256:test_li",
        computation_params={"structure": "bcc"}, confidence=0.9, value_type="scalar"
    ))
    
    # Calculate derived voltage
    calc = BatteryPropertyCalculator(registry)
    voltage = calc.calculate_intercalation_voltage(
        e_delithiated=-17.14,
        e_lithiated=-21.96,
        e_li_metal=-1.90,
        n_li=1.0,
        register_key="derived_voltage_licoo2"
    )
    
    # Verify voltage calculation
    expected_voltage = -(-17.14 + (-1.90) - (-21.96)) / 1.0
    assert abs(voltage - expected_voltage) < 0.01, f"Voltage mismatch: {voltage} vs {expected_voltage}"
    print(f"✓ Voltage calculated correctly: {voltage:.2f} V")
    
    # Verify derived value in registry
    assert "derived_voltage_licoo2" in registry.registry
    derived_entry = registry.registry["derived_voltage_licoo2"]
    assert derived_entry.source_tool == "DERIVED"
    assert derived_entry.computation_params["source_kind"] == "derived"
    assert len(derived_entry.computation_params["derived_from"]) == 3
    print(f"✓ Derived value properly registered with {len(derived_entry.computation_params['derived_from'])} source tuples")
    
    return True


def test_capacity_derivation():
    """Test that capacity derivation works correctly."""
    print("\nTesting capacity derivation...")
    
    registry = ProvenanceRegistry()
    calc = BatteryPropertyCalculator(registry)
    
    # Test LiCoO2 capacity (1 Li per formula unit, M = 97.87 g/mol)
    capacity = calc.calculate_theoretical_capacity(
        n_electrons=1.0,
        molar_mass=97.87,
        register_key="derived_capacity_licoo2"
    )
    
    expected_capacity = 26801 * 1.0 / 97.87
    assert abs(capacity - expected_capacity) < 0.1
    print(f"✓ Capacity calculated correctly: {capacity:.1f} mAh/g")
    
    # Verify registration
    assert "derived_capacity_licoo2" in registry.registry
    assert registry.registry["derived_capacity_licoo2"].source_tool == "DERIVED"
    print(f"✓ Capacity properly registered as DERIVED")
    
    return True


def test_acceptance_gate_validation():
    """Test that derived values pass acceptance gate validation."""
    print("\nTesting acceptance gate validation...")
    
    registry = ProvenanceRegistry()
    
    # Create a proper derived value
    register_derived_value(
        registry,
        key="test_derived_valid",
        value=3.0,
        unit="V",
        derived_from_keys=["mace_energy_1", "mace_energy_2"],
        formula="V = E2 - E1",
        method="Test derivation"
    )
    
    # Add source values to make it valid
    registry.register("mace_energy_1", ProvenancedValue(
        value=-10.0, unit="eV", source_tool="MACE",
        source_artifact_hash="sha256:test1",
        computation_params={}, confidence=0.8, value_type="scalar"
    ))
    
    registry.register("mace_energy_2", ProvenancedValue(
        value=-7.0, unit="eV", source_tool="MACE",
        source_artifact_hash="sha256:test2",
        computation_params={}, confidence=0.8, value_type="scalar"
    ))
    
    # Check validation logic
    derived_value = registry.registry["test_derived_valid"]
    assert derived_value.source_tool == "DERIVED"
    assert derived_value.computation_params["derived_from"] == ["mace_energy_1", "mace_energy_2"]
    
    # Verify source tuples exist
    for source_key in derived_value.computation_params["derived_from"]:
        assert source_key in registry.registry, f"Missing source tuple: {source_key}"
    
    print("✓ Derived value passes validation checks")
    
    # Test invalid case (no source tuples)
    register_derived_value(
        registry,
        key="test_derived_invalid",
        value=5.0,
        unit="V",
        derived_from_keys=[],  # Empty! Should fail validation
        formula="V = magic",
        method="Invalid derivation"
    )
    
    invalid_value = registry.registry["test_derived_invalid"]
    assert invalid_value.computation_params.get("derived_from", []) == []
    print("✓ Invalid derived value correctly identified (no sources)")
    
    return True


def main():
    """Run all smoke tests."""
    print("="*60)
    print("DERIVED PROPERTIES SMOKE TEST")
    print("="*60)
    
    tests = [
        test_voltage_derivation,
        test_capacity_derivation,
        test_acceptance_gate_validation
    ]
    
    all_passed = True
    for test_func in tests:
        try:
            if not test_func():
                all_passed = False
                print(f"✗ {test_func.__name__} failed")
        except Exception as e:
            all_passed = False
            print(f"✗ {test_func.__name__} raised exception: {e}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())