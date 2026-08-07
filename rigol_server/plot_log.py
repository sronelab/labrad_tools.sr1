import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

def get_latest_log_file(extension="*.jsonl"):
    """Finds the most recently modified file with the given extension in the current directory."""
    list_of_files = glob.glob(extension)
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)

def plot_scope_data(filepath):
    print(f"Loading data from: {filepath}")
    
    df = pd.read_json(filepath, lines=True)
    
    if df.empty:
        print("The data file is empty.")
        return

    # Convert timestamps to elapsed seconds
    df['time'] = pd.to_datetime(df['time'], format="%Y-%m-%d %H:%M:%S")
    df['elapsed_seconds'] = (df['time'] - df['time'].iloc[0]).dt.total_seconds()

    # ==========================================
    # DATA PROCESSING: Fractional Units
    # ==========================================
    
    # Method A: Scale relative to the mean value
    ch1_mean_frac = df['ch1_mean'] / df['ch1_mean'].mean()
    ch3_mean_frac = df['ch3_mean'] / df['ch3_mean'].mean()
    ch4_mean_frac = df['ch4_mean'] / df['ch4_mean'].mean()

    ch1_rms = df['ch1_rms']
    ch3_rms = df['ch3_rms']
    ch4_rms = df['ch4_rms']

    # Method B (Optional): Fractional change relative to the first 10 baseline points (ΔV / V0)
    # baseline_clock = df['clock_pulse_mean'].head(10).mean()
    # df['clock_mean_frac'] = (df['clock_pulse_mean'] - baseline_clock) / baseline_clock

    # Create the plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # --- PLOT 1: RMS Voltage (Fractional) ---
    ax1.plot(df['elapsed_seconds'], ch1_rms, label='CH1', color='#1f77b4', linewidth=1.5)
    ax1.plot(df['elapsed_seconds'], ch3_rms, label='CH3', color='#ff7f0e', linewidth=1.5)
    ax1.plot(df['elapsed_seconds'], ch4_rms, label='CH4', color='#2ca02c', linewidth=1.5)
    
    ax1.set_ylabel('RMS Signal', fontsize=12) # Updated label
    ax1.set_title('Scope Log: RMS vs. Time', fontsize=14, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, linestyle='--', alpha=0.7)

    # --- PLOT 2: Mean Voltage (Fractional Units) ---
    ax2.plot(df['elapsed_seconds'], ch1_mean_frac, label='CH1', color='#1f77b4', linewidth=1.5)
    ax2.plot(df['elapsed_seconds'], ch3_mean_frac, label='CH3', color='#ff7f0e', linewidth=1.5)
    ax2.plot(df['elapsed_seconds'], ch4_mean_frac, label='CH4', color='#2ca02c', linewidth=1.5)
    
    ax2.set_xlabel('Time [seconds]', fontsize=12)
    ax2.set_ylabel('Mean Signal [Fractional]', fontsize=12) 
    ax2.set_title('Scope Log: Mean vs. Time (Normalized)', fontsize=14, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    latest_file = get_latest_log_file("*.jsonl")
    latest_file = "scope_log_2026-03-09_15-43-47.jsonl"  # For testing with a specific file
    
    if latest_file:
        plot_scope_data(latest_file)
    else:
        print("No .jsonl log files found in the current directory.")