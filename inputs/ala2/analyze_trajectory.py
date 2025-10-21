#!/usr/bin/env python3
"""
Analysis script for Alanine Dipeptide MD simulation
Calculates phi and psi dihedral angles and creates Ramachandran plot
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import argparse
import sys

def read_xyz_trajectory(filename):
    """Read XYZ trajectory file and return coordinates"""
    coordinates = []
    with open(filename, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            
            # Read number of atoms
            try:
                natoms = int(line.strip())
            except ValueError:
                break
            
            # Skip comment line
            f.readline()
            
            # Read coordinates for this frame
            frame_coords = []
            for i in range(natoms):
                line = f.readline().strip().split()
                if len(line) >= 4:
                    x, y, z = float(line[1]), float(line[2]), float(line[3])
                    frame_coords.append([x, y, z])
            
            coordinates.append(np.array(frame_coords))
    
    return np.array(coordinates)

def calculate_dihedral(p1, p2, p3, p4):
    """Calculate dihedral angle between four points"""
    b1 = p2 - p1
    b2 = p3 - p2
    b3 = p4 - p3
    
    # Normalize b2
    b2_norm = b2 / np.linalg.norm(b2)
    
    # Vector projections
    v = b1 - np.dot(b1, b2_norm) * b2_norm
    w = b3 - np.dot(b3, b2_norm) * b2_norm
    
    # Angle between projections
    x = np.dot(v, w)
    y = np.dot(np.cross(b2_norm, v), w)
    
    return np.degrees(np.arctan2(y, x))

def analyze_alanine_dipeptide(coordinates):
    """
    Analyze alanine dipeptide trajectory
    Atom indices for phi and psi angles (0-indexed):
    - phi: C(ACE) - N(ALA) - CA(ALA) - C(ALA) = atoms 0, 7, 9, 15
    - psi: N(ALA) - CA(ALA) - C(ALA) - N(NME) = atoms 7, 9, 15, 17
    """
    phi_angles = []
    psi_angles = []
    
    for frame in coordinates:
        # Calculate phi angle (C-N-CA-C)
        phi = calculate_dihedral(frame[0], frame[7], frame[9], frame[15])
        phi_angles.append(phi)
        
        # Calculate psi angle (N-CA-C-N)
        psi = calculate_dihedral(frame[7], frame[9], frame[15], frame[17])
        psi_angles.append(psi)
    
    return np.array(phi_angles), np.array(psi_angles)

def create_ramachandran_plot(phi_angles, psi_angles, output_file='ramachandran.png'):
    """Create Ramachandran plot"""
    plt.figure(figsize=(10, 8))
    
    # Create 2D histogram
    plt.hist2d(phi_angles, psi_angles, bins=50, cmap='Blues', alpha=0.7)
    plt.colorbar(label='Frequency')
    
    # Scatter plot overlay
    plt.scatter(phi_angles, psi_angles, alpha=0.3, s=1, color='red')
    
    plt.xlabel('Phi angle (degrees)', fontsize=12)
    plt.ylabel('Psi angle (degrees)', fontsize=12)
    plt.title('Ramachandran Plot - Alanine Dipeptide', fontsize=14)
    
    # Set axis limits
    plt.xlim(-180, 180)
    plt.ylim(-180, 180)
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Mark common secondary structures
    plt.axvline(-60, color='black', linestyle='--', alpha=0.5, label='α-helix region')
    plt.axhline(-45, color='black', linestyle='--', alpha=0.5)
    
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Ramachandran plot saved as {output_file}")

def calculate_statistics(phi_angles, psi_angles):
    """Calculate and print statistics"""
    print("\n=== Dihedral Angle Statistics ===")
    print(f"Phi angle:")
    print(f"  Mean: {np.mean(phi_angles):.2f}°")
    print(f"  Std:  {np.std(phi_angles):.2f}°")
    print(f"  Min:  {np.min(phi_angles):.2f}°")
    print(f"  Max:  {np.max(phi_angles):.2f}°")
    
    print(f"\nPsi angle:")
    print(f"  Mean: {np.mean(psi_angles):.2f}°")
    print(f"  Std:  {np.std(psi_angles):.2f}°")
    print(f"  Min:  {np.min(psi_angles):.2f}°")
    print(f"  Max:  {np.max(psi_angles):.2f}°")
    
    # Save data to file
    data = np.column_stack((phi_angles, psi_angles))
    np.savetxt('dihedral_angles.dat', data, header='Phi(deg) Psi(deg)', fmt='%.2f')
    print(f"\nDihedral angles saved to dihedral_angles.dat")

def main():
    parser = argparse.ArgumentParser(description='Analyze alanine dipeptide MD trajectory')
    parser.add_argument('trajectory', help='XYZ trajectory file')
    parser.add_argument('-o', '--output', default='ramachandran.png', 
                       help='Output plot filename')
    
    args = parser.parse_args()
    
    print(f"Reading trajectory from {args.trajectory}...")
    try:
        coordinates = read_xyz_trajectory(args.trajectory)
        print(f"Loaded {len(coordinates)} frames with {len(coordinates[0])} atoms each")
        
        print("Calculating dihedral angles...")
        phi_angles, psi_angles = analyze_alanine_dipeptide(coordinates)
        
        print("Creating Ramachandran plot...")
        create_ramachandran_plot(phi_angles, psi_angles, args.output)
        
        calculate_statistics(phi_angles, psi_angles)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()