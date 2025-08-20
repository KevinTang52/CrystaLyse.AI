"""
Derived property calculations with full provenance tracking.

Allows auditable derivation of battery metrics from fundamental tool outputs.
"""

import hashlib
from typing import Optional, List, Dict, Any
from provenance_system import ProvenanceRegistry, ProvenancedValue


def register_derived_value(
    registry: ProvenanceRegistry,
    key: str,
    value: float,
    unit: str,
    derived_from_keys: List[str],
    formula: str,
    method: str,
    assumptions: Optional[Dict[str, Any]] = None,
    confidence: Optional[float] = None,
) -> None:
    """Register a derived value with full provenance tracking.
    
    Args:
        registry: Provenance registry to store the value
        key: Unique identifier for this derived value
        value: The computed value
        unit: Physical units
        derived_from_keys: List of source tuple keys used in derivation
        formula: Human-readable formula (e.g., "V = -ΔE/n")
        method: Brief description of calculation method
        assumptions: Optional dict of assumptions made
        confidence: Optional confidence score (0-1)
    """
    # Create hash from derivation details for auditability
    derivation_str = f"{key}:{formula}:{sorted(derived_from_keys)}"
    artifact_hash = f"sha256:{hashlib.sha256(derivation_str.encode()).hexdigest()}"
    
    registry.register(
        key,
        ProvenancedValue(
            value=value,
            unit=unit,
            source_tool="DERIVED",
            source_artifact_hash=artifact_hash,
            computation_params={
                "derived_from": derived_from_keys,
                "formula": formula,
                "method": method,
                "assumptions": assumptions or {},
                "source_kind": "derived",
            },
            confidence=confidence,
            value_type="scalar",
        )
    )


class BatteryPropertyCalculator:
    """Calculate battery properties from fundamental tool outputs."""
    
    def __init__(self, registry: ProvenanceRegistry):
        self.registry = registry
    
    def calculate_intercalation_voltage(
        self,
        e_delithiated: float,  # Energy of delithiated host (eV)
        e_lithiated: float,    # Energy of lithiated host (eV)
        e_li_metal: float,      # Energy of Li metal per atom (eV)
        n_li: float = 1.0,      # Number of Li atoms transferred
        register_key: Optional[str] = None,
    ) -> float:
        """Calculate average intercalation voltage.
        
        V = -(E_delithiated + n*E_Li - E_lithiated) / n  [eV -> V]
        """
        delta_e = e_delithiated + n_li * e_li_metal - e_lithiated
        voltage = -delta_e / n_li  # eV per electron = voltage in V
        
        if register_key:
            register_derived_value(
                self.registry,
                key=register_key,
                value=voltage,
                unit="V",
                derived_from_keys=[
                    "mace_energy_delithiated",
                    "mace_energy_lithiated", 
                    "mace_energy_li_metal"
                ],
                formula="V = -(E_delith + n*E_Li - E_lith) / n",
                method="Average voltage from DFT energies",
                assumptions={
                    "temperature": "0K",
                    "entropy": "neglected",
                    "volume_work": "PV term neglected"
                },
                confidence=0.8  # Typical DFT accuracy
            )
        
        return voltage
    
    def calculate_volume_change(
        self,
        v_initial: float,   # Initial volume (Å³)
        v_final: float,     # Final volume (Å³)
        register_key: Optional[str] = None,
    ) -> float:
        """Calculate volume change percentage.
        
        ΔV% = 100 * (V_final - V_initial) / V_initial
        """
        delta_v_pct = 100 * (v_final - v_initial) / v_initial
        
        if register_key:
            register_derived_value(
                self.registry,
                key=register_key,
                value=delta_v_pct,
                unit="%",
                derived_from_keys=[
                    "chemeleon_volume_initial",
                    "chemeleon_volume_final"
                ],
                formula="ΔV% = 100*(V_f - V_i)/V_i",
                method="Volume change from relaxed structures",
                confidence=0.7  # Structure prediction uncertainty
            )
        
        return delta_v_pct
    
    def calculate_theoretical_capacity(
        self,
        n_electrons: float,    # Electrons transferred per formula unit
        molar_mass: float,     # Molar mass (g/mol)
        register_key: Optional[str] = None,
    ) -> float:
        """Calculate theoretical gravimetric capacity.
        
        C = 26801 * n / M  [mAh/g]
        
        Where 26801 = F/3.6 (Faraday constant / 3.6)
        """
        capacity = 26801 * n_electrons / molar_mass
        
        if register_key:
            register_derived_value(
                self.registry,
                key=register_key,
                value=capacity,
                unit="mAh/g",
                derived_from_keys=["smact_composition_validation"],
                formula="C = 26801*n/M",
                method="Theoretical capacity from stoichiometry",
                assumptions={"electron_transfer": f"{n_electrons} per f.u."},
                confidence=1.0  # Exact from stoichiometry
            )
        
        return capacity
    
    def calculate_volumetric_capacity(
        self,
        gravimetric_capacity: float,  # mAh/g
        density: float,                # g/cm³
        register_key: Optional[str] = None,
    ) -> float:
        """Calculate volumetric capacity from gravimetric.
        
        C_v = C_g * ρ  [mAh/g * g/cm³ = mAh/cm³ = Ah/L]
        """
        volumetric_capacity = gravimetric_capacity * density  # Ah/L
        
        if register_key:
            register_derived_value(
                self.registry,
                key=register_key,
                value=volumetric_capacity,
                unit="Ah/L",
                derived_from_keys=[
                    "derived_capacity_gravimetric",
                    "derived_density"
                ],
                formula="C_v = C_g * ρ",
                method="Volumetric capacity from density",
                confidence=0.8
            )
        
        return volumetric_capacity
    
    def calculate_specific_energy(
        self,
        capacity: float,    # mAh/g
        voltage: float,     # V
        register_key: Optional[str] = None,
    ) -> float:
        """Calculate specific energy.
        
        E_spec = C * V / 1000  [mAh/g * V = mWh/g = Wh/kg]
        """
        specific_energy = capacity * voltage / 1000
        
        if register_key:
            register_derived_value(
                self.registry,
                key=register_key,
                value=specific_energy,
                unit="Wh/kg",
                derived_from_keys=[
                    "derived_capacity_gravimetric",
                    "derived_voltage"
                ],
                formula="E = C*V/1000",
                method="Specific energy from capacity and voltage",
                confidence=0.7
            )
        
        return specific_energy
    
    def calculate_density(
        self,
        mass: float,        # g/mol
        volume: float,      # Å³ per formula unit
        n_fu: float = 1,    # Formula units per cell
        register_key: Optional[str] = None,
    ) -> float:
        """Calculate density from structure.
        
        ρ = M / (N_A * V * 10^-24)  [g/cm³]
        
        Where N_A = 6.022e23 (Avogadro's number)
        """
        avogadro = 6.022e23
        density = (mass * n_fu) / (avogadro * volume * 1e-24)
        
        if register_key:
            register_derived_value(
                self.registry,
                key=register_key,
                value=density,
                unit="g/cm³",
                derived_from_keys=["chemeleon_volume", "smact_composition"],
                formula="ρ = M/(N_A*V*10^-24)",
                method="Density from crystal structure",
                confidence=0.8
            )
        
        return density


# Helper functions for common battery metrics
def compute_battery_metrics(
    registry: ProvenanceRegistry,
    lithiated_energy: float,
    delithiated_energy: float,
    li_metal_energy: float,
    lithiated_volume: float,
    delithiated_volume: float,
    lithiated_mass: float,
    delithiated_mass: float,
    n_li_transferred: float = 1.0,
    material_name: str = "material",
) -> Dict[str, float]:
    """Compute full set of battery metrics with provenance.
    
    Returns dict with:
        - voltage: Average intercalation voltage (V)
        - capacity_grav: Gravimetric capacity (mAh/g)
        - capacity_vol: Volumetric capacity (Ah/L)
        - volume_change: Volume change (%)
        - specific_energy: Specific energy (Wh/kg)
        - energy_density: Energy density (Wh/L)
    """
    calc = BatteryPropertyCalculator(registry)
    
    # Calculate voltage
    voltage = calc.calculate_intercalation_voltage(
        e_delithiated=delithiated_energy,
        e_lithiated=lithiated_energy,
        e_li_metal=li_metal_energy,
        n_li=n_li_transferred,
        register_key=f"derived_voltage_{material_name}"
    )
    
    # Calculate volume change
    volume_change = calc.calculate_volume_change(
        v_initial=lithiated_volume,
        v_final=delithiated_volume,
        register_key=f"derived_volume_change_{material_name}"
    )
    
    # Calculate densities
    density_lithiated = calc.calculate_density(
        mass=lithiated_mass,
        volume=lithiated_volume,
        register_key=f"derived_density_lithiated_{material_name}"
    )
    
    # Calculate capacities
    capacity_grav = calc.calculate_theoretical_capacity(
        n_electrons=n_li_transferred,
        molar_mass=lithiated_mass,
        register_key=f"derived_capacity_grav_{material_name}"
    )
    
    capacity_vol = calc.calculate_volumetric_capacity(
        gravimetric_capacity=capacity_grav,
        density=density_lithiated,
        register_key=f"derived_capacity_vol_{material_name}"
    )
    
    # Calculate energy metrics
    specific_energy = calc.calculate_specific_energy(
        capacity=capacity_grav,
        voltage=voltage,
        register_key=f"derived_specific_energy_{material_name}"
    )
    
    energy_density = capacity_vol * voltage  # Wh/L
    register_derived_value(
        registry,
        key=f"derived_energy_density_{material_name}",
        value=energy_density,
        unit="Wh/L",
        derived_from_keys=[
            f"derived_capacity_vol_{material_name}",
            f"derived_voltage_{material_name}"
        ],
        formula="E_d = C_v * V",
        method="Energy density from volumetric capacity",
        confidence=0.7
    )
    
    return {
        "voltage": voltage,
        "capacity_grav": capacity_grav,
        "capacity_vol": capacity_vol,
        "volume_change": volume_change,
        "specific_energy": specific_energy,
        "energy_density": energy_density,
    }