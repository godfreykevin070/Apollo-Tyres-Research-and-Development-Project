#!/usr/bin/env python
"""
Extract data from Abaqus ODB file and save as CSV.
Usage: abaqus python extract_odb_data.py <odb_path> <output_dir>
"""
import sys
import os
import csv
from odbAccess import openOdb

def extract_odb_data(odb_path, output_dir):
    """Extract field data from ODB and save to CSV files"""
    if not os.path.exists(odb_path):
        print(f"Error: ODB file not found: {odb_path}")
        return 1
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Open ODB
    try:
        odb = openOdb(odb_path)
    except Exception as e:
        print(f"Error opening ODB: {e}")
        return 1
    
    # Get steps
    steps = odb.steps.values()
    if not steps:
        print("No steps found in ODB")
        odb.close()
        return 1
    
    # For each step, extract history output (time history)
    for step in steps:
        print(f"Processing step: {step.name}")
        # Get history regions
        for region in step.historyRegions.values():
            region_name = region.name
            print(f"  Region: {region_name}")
            
            # Get output variables
            for var_name, var_data in region.historyOutputs.items():
                print(f"    Variable: {var_name}")
                # Save to CSV
                csv_path = os.path.join(output_dir, f"{var_name}.csv")
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['time', 'value'])
                    for data_point in var_data.data:
                        writer.writerow([data_point.time, data_point.value])
                print(f"      Saved to {csv_path}")
    
    odb.close()
    print("Extraction complete")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: abaqus python extract_odb_data.py <odb_path> <output_dir>")
        sys.exit(1)
    
    odb_path = sys.argv[1]
    output_dir = sys.argv[2]
    sys.exit(extract_odb_data(odb_path, output_dir))