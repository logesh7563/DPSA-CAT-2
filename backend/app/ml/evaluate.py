"""
Evaluation and Metrics Calculation Module
Reports Macro-F1, Per-Class Recall, Precision, Confusion Matrix, and Accuracy.
"""

from typing import Dict, List
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score

from app.ml.schema import CLASS_NAMES, NUM_CLASSES


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    """
    Computes federated security analytics metrics:
    - Macro-F1 (unweighted average across all 5 classes)
    - Per-Class Recall (detection rate for Normal, DoS, Probe, R2L, U2R)
    - Per-Class Precision
    - Per-Class F1
    - 5x5 Confusion Matrix
    - Accuracy
    """
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    accuracy = float(np.mean(y_true == y_pred))

    recalls = recall_score(y_true, y_pred, average=None, labels=list(range(NUM_CLASSES)), zero_division=0)
    precisions = precision_score(y_true, y_pred, average=None, labels=list(range(NUM_CLASSES)), zero_division=0)
    f1s = f1_score(y_true, y_pred, average=None, labels=list(range(NUM_CLASSES)), zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(NUM_CLASSES)))

    per_class = {}
    for i, name in enumerate(CLASS_NAMES):
        per_class[name] = {
            "recall": float(recalls[i]),
            "precision": float(precisions[i]),
            "f1": float(f1s[i]),
            "support": int(np.sum(y_true == i))
        }

    return {
        "macro_f1": macro_f1,
        "accuracy": accuracy,
        "per_class": per_class,
        "per_class_recall": {name: float(recalls[i]) for i, name in enumerate(CLASS_NAMES)},
        "confusion_matrix": cm.tolist()
    }


def evaluate_model_on_loader(
    model: nn.Module,
    dataloader,
    device: torch.device = torch.device("cpu")
) -> Dict:
    """Evaluates a PyTorch model on a DataLoader."""
    model.eval()
    all_preds = []
    all_targets = []
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss()

    with torch.no_grad():
        for X_b, y_b in dataloader:
            X_b, y_b = X_b.to(device), y_b.to(device)
            outputs = model(X_b)
            loss = criterion(outputs, y_b)
            total_loss += loss.item() * len(y_b)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(y_b.cpu().numpy())

    total_samples = len(all_targets)
    avg_loss = total_loss / max(1, total_samples)

    metrics = evaluate_predictions(np.array(all_targets), np.array(all_preds))
    metrics["loss"] = float(avg_loss)
    return metrics
