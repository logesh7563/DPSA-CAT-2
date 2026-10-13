"""
Federated Preprocessing, Dataloader, and Evaluation Module
Course: Data Privacy and Security Analytics (DPSA) - CAT-2
Dataset: NSL-KDD

Guarantees:
1. Federated-Safe Preprocessing:
   - Fixed categorical domains for protocol_type, service, and flag.
   - Guaranteed identical feature dimension (122 features) across all clients and test set.
   - Local per-client scaling (fit strictly on client's local train set) or fixed domain scaling to prevent statistical leakage.
2. Local Validation Splits:
   - Client datasets are split locally (e.g. 80/20 train/val) for per-client validation metrics.
   - KDDTest+ remains an independent global test set.
3. Class Imbalance Handling:
   - Client-specific balanced class weights for PyTorch weighted CrossEntropyLoss.
   - No SMOTE or synthetic oversampling on low-sample classes (e.g. U2R on Client 2).
4. Comprehensive Metrics:
   - Macro-F1, Per-Class Recall (Normal, DoS, Probe, R2L, U2R), and Confusion Matrix.
5. Difficulty-level column is dropped from all feature vectors.
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score, recall_score
import torch
from torch.utils.data import Dataset, DataLoader

# Base paths
MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parent
SPLITS_DIR = MODULE_DIR / "client_splits"
TEST_FILE = SPLITS_DIR / "test_set.csv"

# 5 Target Macro Classes
CLASS_NAMES = ["Normal", "DoS", "Probe", "R2L", "U2R"]
NUM_CLASSES = 5

# Fixed category domains from official NSL-KDD specification
# Ensures all clients produce identical one-hot feature columns regardless of local traffic
FIXED_CATEGORIES = {
    "protocol_type": ["icmp", "tcp", "udp"],
    "service": [
        "aol", "auth", "bgp", "courier", "csnet_ns", "ctf", "daytime", "discard",
        "domain", "domain_u", "echo", "eco_i", "ecr_i", "efs", "exec", "finger",
        "ftp", "ftp_data", "gopher", "harvest", "hostnames", "http", "http_2784",
        "http_443", "http_8001", "imap4", "IRC", "iso_tsap", "klogin", "kshell",
        "ldap", "link", "login", "mtp", "name", "netbios_dgm", "netbios_ns",
        "netbios_ssn", "netstat", "nnsp", "nntp", "ntp_u", "other", "pm_dump",
        "pop_2", "pop_3", "printer", "private", "red_i", "remote_job", "rje",
        "shell", "smtp", "sql_net", "ssh", "sunrpc", "supdup", "systat", "telnet",
        "tftp_u", "tim_i", "time", "urh_i", "urp_i", "uucp", "uucp_path", "vmnet",
        "whois", "X11", "Z39_50"
    ],
    "flag": [
        "OTH", "REJ", "RSTO", "RSTOS0", "RSTR", "S0", "S1", "S2", "S3", "SF", "SH"
    ]
}

# 38 Numerical / continuous / binary network features
NUMERICAL_FEATURES = [
    "duration", "src_bytes", "dst_bytes", "land", "wrong_fragment", "urgent",
    "hot", "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login", "is_guest_login",
    "count", "srv_count", "serror_rate", "srv_serror_rate", "rerror_rate",
    "srv_rerror_rate", "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate",
    "dst_host_count", "dst_host_srv_count", "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate", "dst_host_srv_rerror_rate"
]

# Total expected features: 3 (protocol) + 70 (service) + 11 (flag) + 38 (numerical) = 122
EXPECTED_NUM_FEATURES = 3 + 70 + 11 + 38  # 122


def encode_features_federated(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encodes categorical features using fixed pre-defined categories.
    Guarantees every client outputs exactly 122 columns in identical order.
    Drops metadata columns (e.g. difficulty_level, attack_type).
    """
    encoded_dfs = []
    
    # 1. One-hot encode categoricals with fixed schema
    for col, categories in FIXED_CATEGORIES.items():
        cat_series = pd.Categorical(df[col], categories=categories)
        dummies = pd.get_dummies(cat_series, prefix=col, dtype=np.float32)
        encoded_dfs.append(dummies)
        
    # 2. Extract numerical features
    num_df = df[NUMERICAL_FEATURES].astype(np.float32).copy()
    encoded_dfs.append(num_df)
    
    # Concatenate all features
    features_df = pd.concat(encoded_dfs, axis=1)
    return features_df


def compute_client_class_weights(y: np.ndarray, num_classes: int = 5, mode: str = "sqrt") -> torch.Tensor:
    """
    Computes balanced class weights for loss function on client data.
    
    Modes:
    - 'balanced': Standard balanced weighting: N / (num_classes * N_c)
    - 'sqrt': Smoothed inverse frequency: sqrt(N / N_c), prevents extreme gradients
              on ultra-rare classes like Client 2's 7 U2R samples while ensuring
              minority classes get a substantial gradient boost.
    """
    total_samples = len(y)
    classes, counts = np.unique(y, return_counts=True)
    count_dict = dict(zip(classes, counts))
    
    weights = np.ones(num_classes, dtype=np.float32)
    for c in range(num_classes):
        if c in count_dict and count_dict[c] > 0:
            count = count_dict[c]
            if mode == "balanced":
                weights[c] = total_samples / (len(classes) * count)
            elif mode == "sqrt":
                weights[c] = np.sqrt(total_samples / count)
        else:
            # Classes not present on this client (e.g. DoS on Client 2)
            weights[c] = 1.0
            
    return torch.tensor(weights, dtype=torch.float32)


class TorchFederatedDataset(Dataset):
    """PyTorch Dataset wrapper for client or test features and labels."""
    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class FederatedClientData:
    """
    Encapsulates a client gateway's localized dataset:
    - Performs local 80/20 stratified train/validation split
    - Fits local StandardScaler ONLY on local train set (zero statistical leakage)
    - Computes local class weights for weighted cross-entropy
    """
    def __init__(self, client_id: int, val_ratio: float = 0.2, seed: int = 42):
        self.client_id = client_id
        self.val_ratio = val_ratio
        self.seed = seed
        self.file_path = SPLITS_DIR / f"client_{client_id}.csv"
        
        # Load local raw data
        raw_df = pd.read_csv(self.file_path)
        
        # Extract labels
        y_all = raw_df["macro_class_id"].values.astype(np.int64)
        
        # Encode features with federated-safe fixed taxonomy
        X_df = encode_features_federated(raw_df)
        X_all = X_df.values.astype(np.float32)
        
        assert X_all.shape[1] == EXPECTED_NUM_FEATURES, (
            f"Expected {EXPECTED_NUM_FEATURES} features, got {X_all.shape[1]}"
        )
        
        # Local train/val split (stratified if possible)
        # Note: If a class has only 1 sample, stratify might fail, so fallback gracefully
        try:
            X_train, X_val, y_train, y_val = train_test_split(
                X_all, y_all, test_size=val_ratio, random_state=seed, stratify=y_all
            )
        except ValueError:
            X_train, X_val, y_train, y_val = train_test_split(
                X_all, y_all, test_size=val_ratio, random_state=seed
            )
            
        # Local per-client scaling: fit ONLY on local X_train
        self.scaler = StandardScaler()
        self.X_train = self.scaler.fit_transform(X_train)
        self.X_val = self.scaler.transform(X_val)
        self.y_train = y_train
        self.y_val = y_val
        
        # Local class weights
        self.class_weights = compute_client_class_weights(self.y_train, NUM_CLASSES)
        
        # PyTorch datasets
        self.train_dataset = TorchFederatedDataset(self.X_train, self.y_train)
        self.val_dataset = TorchFederatedDataset(self.X_val, self.y_val)
        
    def get_dataloaders(self, batch_size: int = 64) -> Tuple[DataLoader, DataLoader]:
        train_loader = DataLoader(self.train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(self.val_dataset, batch_size=batch_size, shuffle=False)
        return train_loader, val_loader


class GlobalTestDatasetManager:
    """
    Encapsulates the independent global test set (KDDTest+):
    - Separate from all client data (no carving from client files).
    - Uses fixed-schema feature encoding (122 features).
    - Can be scaled using a reference scaler or client-specific scaler.
    """
    def __init__(self, test_csv_path: Optional[Path] = None):
        self.test_csv_path = test_csv_path or TEST_FILE
        raw_df = pd.read_csv(self.test_csv_path)
        
        self.y_test = raw_df["macro_class_id"].values.astype(np.int64)
        X_df = encode_features_federated(raw_df)
        self.X_raw = X_df.values.astype(np.float32)
        
        assert self.X_raw.shape[1] == EXPECTED_NUM_FEATURES, (
            f"Expected {EXPECTED_NUM_FEATURES} features, got {self.X_raw.shape[1]}"
        )
        
    def get_dataloader(self, scaler: StandardScaler, batch_size: int = 128) -> DataLoader:
        X_scaled = scaler.transform(self.X_raw)
        dataset = TorchFederatedDataset(X_scaled, self.y_test)
        return DataLoader(dataset, batch_size=batch_size, shuffle=False)


def evaluate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    """
    Calculates federated evaluation metrics:
    - Macro-F1: unweighted mean across all 5 classes
    - Per-class Recall: individual True Positive rates (crucial for rare classes like U2R & R2L)
    - Confusion Matrix (5x5)
    - Accuracy (reported with caveats)
    """
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    per_class_recalls = recall_score(y_true, y_pred, average=None, labels=list(range(NUM_CLASSES)), zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(NUM_CLASSES)))
    acc = np.mean(y_true == y_pred)
    
    recall_dict = {CLASS_NAMES[i]: float(per_class_recalls[i]) for i in range(NUM_CLASSES)}
    
    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "per_class_recall": recall_dict,
        "confusion_matrix": cm.tolist()
    }


def print_evaluation_report(metrics: Dict, title: str = "EVALUATION REPORT"):
    """Displays a formatted evaluation report with macro-F1 and per-class recall."""
    print("=" * 70)
    print(f" {title}")
    print("=" * 70)
    print(f" Macro-F1 Score : {metrics['macro_f1']:.4f}  (PRIMARY OPTIMIZATION METRIC)")
    print(f" Overall Accuracy: {metrics['accuracy'] * 100:.2f}%  (Baseline reference)")
    print("-" * 70)
    print(" Per-Class Recall (Detection Rate):")
    for cls_name, recall in metrics["per_class_recall"].items():
        print(f"   - {cls_name:<8}: {recall * 100:6.2f}%")
    print("-" * 70)
    print(" 5x5 Confusion Matrix (Rows: Actual, Cols: Predicted):")
    cm = np.array(metrics["confusion_matrix"])
    header = "       " + " ".join([f"{c:>7}" for c in CLASS_NAMES])
    print(header)
    for i, row in enumerate(cm):
        row_str = f"{CLASS_NAMES[i]:<7}" + " ".join([f"{val:>7d}" for val in row])
        print(row_str)
    print("=" * 70)


if __name__ == "__main__":
    print("[1/3] Testing Federated Client Loading & Preprocessing...")
    for c_id in range(4):
        c_data = FederatedClientData(client_id=c_id)
        print(f"  Client {c_id}:")
        print(f"    Train size: {len(c_data.X_train)}, Val size: {len(c_data.X_val)}")
        print(f"    Feature dimension: {c_data.X_train.shape[1]} (Federated-safe match)")
        print(f"    Class weights (0-4): {np.round(c_data.class_weights.numpy(), 2)}")
        
    print("\n[2/3] Testing Global Test Set (KDDTest+) Loading...")
    test_mgr = GlobalTestDatasetManager()
    print(f"  Global Test Samples: {len(test_mgr.y_test)}")
    print(f"  Feature dimension  : {test_mgr.X_raw.shape[1]}")
    
    print("\n[3/3] Testing Metric Evaluation Output...")
    dummy_true = np.array([0, 1, 2, 3, 4] * 20)
    dummy_pred = np.array([0, 1, 2, 0, 0] * 20)  # Fails completely on R2L and U2R
    metrics = evaluate_metrics(dummy_true, dummy_pred)
    print_evaluation_report(metrics, title="Sample Synthetic Metric Check")
