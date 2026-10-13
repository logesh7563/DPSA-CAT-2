"""
Data Preparation and Federated Splitting Module
Course: Data Privacy and Security Analytics (DPSA) - CAT-2
Dataset: NSL-KDD

This script:
1. Loads the NSL-KDD dataset with correct headers.
2. Maps fine-grained attack types to 5 standard classes:
   - 0: Normal (Benign traffic)
   - 1: DoS (Denial of Service)
   - 2: Probe (Port scan / Reconnaissance)
   - 3: R2L (Remote to Local)
   - 4: U2R (User to Root)
3. Implements realistic Enterprise Non-IID splitting across 4 client gateways:
   - Client 0 (Web Gateway): Skewed towards DoS attacks
   - Client 1 (Edge Perimeter Router): Skewed towards Probe scans
   - Client 2 (Internal Corporate LAN): Benign traffic + R2L/U2R (0 DoS, 0 Probe)
   - Client 3 (Branch Office): Mixed baseline traffic
4. Saves the split partitions to CSV files for each client and outputs summary statistics.
"""

import os
import json
from pathlib import Path
from collections import defaultdict
import pandas as pd
import numpy as np

# Base paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DATA_DIR = PROJECT_ROOT / "NSL-KDD-DataSet"
OUTPUT_DIR = CURRENT_DIR / "client_splits"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Dataset file paths
TRAIN_FILE = DATA_DIR / "KDDTrain+_20Percent.txt"
FULL_TRAIN_FILE = DATA_DIR / "KDDTrain+.txt"
TEST_FILE = DATA_DIR / "KDDTest+.txt"
ATTACK_TYPES_FILE = DATA_DIR / "attack_types.txt"

# Official 41 NSL-KDD column names + labels
COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes",
    "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
    "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate", "attack_type", "difficulty_level"
]

CLASS_NAMES = ["Normal", "DoS", "Probe", "R2L", "U2R"]

ATTACK_CATEGORIES = {
    "normal": 0,
    "dos": 1,
    "probe": 2,
    "r2l": 3,
    "u2r": 4
}


def load_attack_mapping():
    """Reads attack_types.txt to map fine-grained attacks to 5 macro categories."""
    mapping = {"normal": "normal"}
    if ATTACK_TYPES_FILE.exists():
        with open(ATTACK_TYPES_FILE, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    mapping[parts[0].lower()] = parts[1].lower()

    # Additional known test-set signatures
    additional = {
        "snmpgetattack": "dos", "mailbomb": "dos", "processtable": "dos",
        "udpstorm": "dos", "apache2": "dos", "worm": "r2l", "xlock": "r2l",
        "xsnoop": "r2l", "ps": "u2r", "mscan": "probe", "saint": "probe",
        "httptunnel": "u2r", "sqlattack": "u2r", "named": "r2l", "sendmail": "r2l"
    }
    for k, v in additional.items():
        if k not in mapping:
            mapping[k] = v

    return mapping


def load_and_label_dataset(file_path):
    """Loads CSV and maps attack_type to standard 5 macro classes."""
    mapping = load_attack_mapping()
    df = pd.read_csv(file_path, names=COLUMNS, header=None)

    def get_category_id(attack):
        clean_name = str(attack).strip().lower()
        cat = mapping.get(clean_name, "normal")
        return ATTACK_CATEGORIES.get(cat, 0)

    def get_category_name(attack):
        cat_id = get_category_id(attack)
        return CLASS_NAMES[cat_id]

    df["macro_class_id"] = df["attack_type"].apply(get_category_id)
    df["macro_class_name"] = df["attack_type"].apply(get_category_name)
    
    # Drop difficulty_level: metadata only, not a network feature
    if "difficulty_level" in df.columns:
        df = df.drop(columns=["difficulty_level"])
        
    return df


def split_non_iid_enterprise(df, num_clients=4, seed=42):
    """
    Splits dataset into 4 realistic non-IID enterprise client partitions:
    - Client 0 (Web Gateway): 75% of DoS attacks
    - Client 1 (Edge Perimeter Router): 75% of Probe scans
    - Client 2 (Internal Corporate LAN): 0 DoS, 0 Probe, high Normal + R2L/U2R
    - Client 3 (Branch Office): Mixed baseline traffic
    """
    np.random.seed(seed)

    # Group indices by attack class id (0 to 4)
    class_indices = defaultdict(list)
    for idx, row in df.iterrows():
        class_indices[row["macro_class_id"]].append(idx)

    # Shuffle indices within each class
    for cat_id in class_indices:
        np.random.shuffle(class_indices[cat_id])

    client_splits = [[] for _ in range(num_clients)]

    # 1. Normal Traffic (Class 0)
    normal = class_indices[0]
    n0 = int(0.20 * len(normal))
    n1 = int(0.40 * len(normal))
    n2 = int(0.75 * len(normal))
    client_splits[0].extend(normal[:n0])
    client_splits[1].extend(normal[n0:n1])
    client_splits[2].extend(normal[n1:n2])
    client_splits[3].extend(normal[n2:])

    # 2. DoS Volumetric Floods (Class 1)
    dos = class_indices[1]
    d0 = int(0.75 * len(dos))
    d1 = int(0.80 * len(dos))
    client_splits[0].extend(dos[:d0])
    client_splits[1].extend(dos[d0:d1])
    # Client 2 receives 0 DoS samples!
    client_splits[3].extend(dos[d1:])

    # 3. Probe Scans (Class 2)
    probe = class_indices[2]
    p0 = int(0.05 * len(probe))
    p1 = int(0.80 * len(probe))
    client_splits[0].extend(probe[:p0])
    client_splits[1].extend(probe[p0:p1])
    # Client 2 receives 0 Probe samples!
    client_splits[3].extend(probe[p1:])

    # 4. R2L (Class 3) & U2R (Class 4) Internal Exploits
    r2l = class_indices[3]
    r_split = int(0.75 * len(r2l))
    client_splits[2].extend(r2l[:r_split])
    client_splits[3].extend(r2l[r_split:])

    u2r = class_indices[4]
    u_split = int(0.70 * len(u2r))
    client_splits[2].extend(u2r[:u_split])
    client_splits[3].extend(u2r[u_split:])

    # Shuffle each client partition
    client_dfs = []
    for c_id in range(num_clients):
        np.random.shuffle(client_splits[c_id])
        client_df = df.iloc[client_splits[c_id]].copy().reset_index(drop=True)
        client_dfs.append(client_df)

    return client_dfs


def main():
    print("=" * 80)
    print(" STEP 1: NSL-KDD DATASET PREPARATION & NON-IID CLIENT SPLITTING")
    print("=" * 80)

    # 1. Load training dataset
    print(f"\n[1/4] Loading training dataset from: {TRAIN_FILE.name}")
    train_df = load_and_label_dataset(TRAIN_FILE)
    print(f"      Total records loaded: {len(train_df):,}")
    print("      Class Distribution in Training Set:")
    for cls in CLASS_NAMES:
        count = (train_df["macro_class_name"] == cls).sum()
        print(f"        - {cls:<8}: {count:>6,} ({count/len(train_df)*100:5.2f}%)")

    # 2. Perform Non-IID Splitting
    print("\n[2/4] Splitting records into 4 Enterprise Client Gateways (Non-IID)...")
    client_dfs = split_non_iid_enterprise(train_df, num_clients=4, seed=42)

    # 3. Save Client Partitions to CSV
    print(f"\n[3/4] Saving split datasets into: {OUTPUT_DIR}")
    gateway_names = [
        "Client 0 (Web Application Gateway)",
        "Client 1 (Edge Perimeter Router)",
        "Client 2 (Internal Corporate LAN)",
        "Client 3 (Regional Branch Office)"
    ]

    partition_stats = {}
    for i, client_df in enumerate(client_dfs):
        filename = f"client_{i}.csv"
        filepath = OUTPUT_DIR / filename
        client_df.to_csv(filepath, index=False)

        dist = {}
        for cls in CLASS_NAMES:
            dist[cls] = int((client_df["macro_class_name"] == cls).sum())

        partition_stats[f"Client_{i}"] = {
            "name": gateway_names[i],
            "file": filename,
            "total_records": len(client_df),
            "distribution": dist
        }
        print(f"      Saved {filename} ({len(client_df):,} records)")

    # 4. Also prepare and save the test set
    print(f"\n[4/4] Preparing independent global test set from: {TEST_FILE.name}")
    test_df = load_and_label_dataset(TEST_FILE)
    test_filepath = OUTPUT_DIR / "test_set.csv"
    test_df.to_csv(test_filepath, index=False)
    print(f"      Saved test_set.csv ({len(test_df):,} records)")

    # Save summary json
    summary_path = OUTPUT_DIR / "split_summary.json"
    with open(summary_path, "w") as f:
        json.dump(partition_stats, f, indent=2)

    # Display clean formatted summary table
    print("\n" + "=" * 80)
    print(" CLIENT PARTITION SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Client Gateway':<35} | {'Total':<6} | {'Normal':<6} | {'DoS':<6} | {'Probe':<6} | {'R2L':<5} | {'U2R':<4}")
    print("-" * 80)
    for i in range(4):
        c_stats = partition_stats[f"Client_{i}"]
        d = c_stats["distribution"]
        print(f"{c_stats['name']:<35} | {c_stats['total_records']:<6} | {d['Normal']:<6} | {d['DoS']:<6} | {d['Probe']:<6} | {d['R2L']:<5} | {d['U2R']:<4}")

    print("\n>>> KEY DPSA PRIVACY OBSERVATION:")
    print("    - Client 2 has 0 DoS and 0 Probe records (Internal LAN blind spot).")
    print("    - Data is completely localized to client_0.csv through client_3.csv.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
