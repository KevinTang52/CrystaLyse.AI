#!/usr/bin/env python3
"""Debug SMACT server startup issues."""

import os
import asyncio
import subprocess
import sys
from pathlib import Path

# Set up environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_MDG_API_KEY", "")


async def test_smact_startup():
    """Test SMACT server startup with detailed debugging."""
    
    print("Debugging SMACT Server Startup...")
    print("=" * 60)
    
    smact_path = Path(__file__).parent / "smact-mcp-server"
    
    # Test 1: Direct Python import
    print("1. Testing direct Python import...")
    try:
        sys.path.insert(0, str(smact_path / "src"))
        from smact_mcp.server_fixed import main
        print("   Direct import successful")
    except Exception as e:
        print(f"   Import error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Test SMACT imports specifically
    print("\n2. Testing SMACT imports...")
    try:
        smact_lib_path = Path(__file__).parent / "smact"
        sys.path.insert(0, str(smact_lib_path))
        
        import smact
        print("   SMACT core imported")
        
        from smact.screening import smact_validity
        print("   SMACT screening imported") 
        
        from smact.utils.composition import parse_formula
        print("   SMACT utils imported")
        
        from pymatgen.core import Composition
        print("   Pymatgen imported")
        
    except Exception as e:
        print(f"   SMACT import error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Test basic SMACT functionality
    print("\n3. Testing basic SMACT functionality...")
    try:
        # Test formula parsing
        result = parse_formula("NaCl")
        print(f"   Formula parsing works: {result}")
        
        # Test composition
        comp = Composition("NaCl")
        print(f"   Composition creation works: {comp}")
        
        # Test validity (might be slow)
        print("   Testing SMACT validity (this may take a moment)...")
        is_valid = smact_validity(comp)
        print(f"   SMACT validity works: {is_valid}")
        
    except Exception as e:
        print(f"   SMACT functionality error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Try running the server in a subprocess with timeout
    print("\n4. Testing server startup in subprocess...")
    try:
        cmd = [sys.executable, "-m", "smact_mcp"]
        process = subprocess.Popen(
            cmd,
            cwd=str(smact_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=3)
            print(f"   Process stdout: {stdout}")
            print(f"   Process stderr: {stderr}")
            print(f"   Process return code: {process.returncode}")
        except subprocess.TimeoutExpired:
            print("   Process timed out (expected for stdio server)")
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=1)
                print(f"   Process stdout: {stdout}")
                print(f"   Process stderr: {stderr}")
            except subprocess.TimeoutExpired:
                print("   Force killing process")
                process.kill()
                
    except Exception as e:
        print(f"   Subprocess error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nSMACT startup debug completed!")


async def main():
    """Main debug function."""
    try:
        await test_smact_startup()
        print("\nDebug completed!")
    except Exception as e:
        print(f"\nDebug failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())