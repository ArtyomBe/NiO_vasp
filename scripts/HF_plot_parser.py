import re
import matplotlib.pyplot as plt

log_path = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/output_analysis/HF_analysis/graphs/processing_log.txt'
output_path = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/output_analysis/HF_analysis/graphs/HF_coordinates.txt'

aexx_values = []
energies = []
band_gaps = []

with open(log_path, 'r') as file:
    current_aexx = None
    for line in file:
        # Match AEXX
        aexx_match = re.search(r"AEXX_(\d+)%", line)
        if aexx_match:
            current_aexx = int(aexx_match.group(1))  # Extract AEXX
        elif current_aexx is not None:
            # Match Energy
            energy_match = re.search(r"Energy:\s*(-?\d+\.\d+)", line)
            # Match Band Gap
            band_gap_match = re.search(r"Band gap:\s*(-?\d+\.\d+)", line)
            if energy_match:
                energies.append(float(energy_match.group(1)))
            if band_gap_match:
                band_gaps.append(float(band_gap_match.group(1)))
                aexx_values.append(current_aexx)  # Save AEXX only when both values are extracted
                current_aexx = None  # Reset for next block

# Sort data by AEXX values
sorted_data = sorted(zip(aexx_values, energies, band_gaps), key=lambda x: x[0])
aexx_values, energies, band_gaps = zip(*sorted_data)

# Save coordinates to file
with open(output_path, 'w') as outfile:
    outfile.write("График 1\n")
    outfile.write("AEXX (%)\tEnergy (eV)\n")
    for x, y in zip(aexx_values, energies):
        outfile.write(f"{x}\t{y}\n")
    outfile.write("\n")

    outfile.write("График 2\n")
    outfile.write("AEXX (%)\tBand Gap (eV)\n")
    for x, y in zip(aexx_values, band_gaps):
        outfile.write(f"{x}\t{y}\n")

# Plot Energy vs AEXX
plt.figure(figsize=(10, 5))
plt.plot(aexx_values, energies, marker='o', label='Energy')
plt.title('Energy vs AEXX')
plt.xlabel('AEXX (%)')
plt.ylabel('Energy (eV)')
plt.grid(True)
plt.legend()
plt.show()

# Plot Band Gap vs AEXX
plt.figure(figsize=(10, 5))
plt.plot(aexx_values, band_gaps, marker='o', color='orange', label='Band Gap')
plt.title('Band Gap vs AEXX')
plt.xlabel('AEXX (%)')
plt.ylabel('Band Gap (eV)')
plt.grid(True)
plt.legend()
plt.show()