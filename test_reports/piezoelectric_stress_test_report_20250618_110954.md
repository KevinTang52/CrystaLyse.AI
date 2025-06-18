# CrystaLyse.AI Piezoelectric Materials Stress Test Report

**Date**: 2025-06-18T11:08:01.665391  
**Test Type**: Piezoelectric Materials Discovery

## Executive Summary

This stress test evaluates CrystaLyse.AI's performance in discovering piezoelectric materials using both Creative and Rigorous modes.

## Test Results

### Creative Mode Test

**Query**: "Explore novel piezoelectric materials"  
**Status**: ✅ Success  
**Execution Time**: 39.76 seconds  
**Model Used**: o4-mini  
**Compositions Generated**: 19

#### Performance Metrics
- Total Cost: $0.000
- Tool Calls: 0
- Success Rate: 0.0%

### Rigorous Mode Test

**Query**: "Find stable lead-free piezoelectric for medical devices"  
**Status**: ✅ Success  
**Execution Time**: 70.97 seconds  
**Model Used**: o3  

#### Validation Metrics
- Compositions Validated: 10
- Structures Predicted: 50
- Energy Calculations: 23

#### Performance Metrics
- Total Cost: $0.000
- Tool Calls: 0
- Success Rate: 0.0%

## Mode Comparison

- **Time Difference**: 31.21 seconds
- **Speedup Factor**: 1.78x
- **Creative Mode Faster By**: 44.0%
- **Validation Overhead**: SMACT validation + structure prediction + energy calculations

### Recommendation
Use Creative Mode for initial exploration, Rigorous Mode for final validation

## Conclusions

1. **Creative Mode** provides rapid exploration of chemical space, ideal for initial discovery
2. **Rigorous Mode** ensures validated results with computational verification
3. The modes are complementary: use Creative for breadth, Rigorous for depth
4. Time-performance trade-off aligns with expected behaviour (~2x slower for full validation)

## Error Summary

No errors encountered during testing. ✅

---
*Report generated on 2025-06-18 11:09:54*
