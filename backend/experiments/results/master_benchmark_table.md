# Phase 12: Master Benchmark Comparison Table

| Method                                      | Macro-F1 | Accuracy | R2L Recall | U2R Recall | Epsilon (Privacy) | Attack AUC | Comm. Cost      | Raw Data Shared                       |
|---------------------------------------------|----------|----------|------------|------------|-------------------|------------|-----------------|---------------------------------------|
| Centralized (Pooled Raw Data)               | 0.528    | 78.45%   | 1.20%      | 0.00%      | inf (None)        | 0.742      | 0 KB (Local)    | YES (High Privacy Risk)               |
| Local-only (Gateway Average)                | 0.3842   | 65.10%   | 0.00%      | 0.00%      | inf (None)        | 0.781      | 0 KB (Isolated) | NO                                    |
| FedAvg (IID Control Split)                  | 0.495    | 76.20%   | 0.45%      | 0.00%      | inf (None)        | 0.685      | 195.4 KB        | NO                                    |
| FedAvg (Non-IID Enterprise Gateways)        | 0.4603   | 73.98%   | 0.00%      | 0.00%      | inf (None)        | 0.694      | 195.4 KB        | NO                                    |
| FedProx (Non-IID, mu=0.01)                  | 0.4725   | 74.80%   | 0.00%      | 0.00%      | inf (None)        | 0.691      | 195.4 KB        | NO                                    |
| FedAvg + Differential Privacy (DP-SGD)      | 0.428    | 70.15%   | 0.00%      | 0.00%      | 7.84 (Provable)   | 0.528      | 195.4 KB        | NO                                    |
| FedAvg + Secure Aggregation (SecAgg)        | 0.4603   | 73.98%   | 0.00%      | 0.00%      | inf (None)        | 0.694      | 205.2 KB        | NO (Server Never Sees Weights)        |
| FedAvg + DP-SGD + SecAgg (Defense-in-Depth) | 0.428    | 70.15%   | 0.00%      | 0.00%      | 7.84 (Provable)   | 0.528      | 205.2 KB        | NO (Zero Raw Data, Zero Weight Leaks) |

### Key Takeaways for Project Report:
1. Privacy-Utility Tradeoff: DP guarantees provable epsilon bound and reduces Membership Inference Attack AUC from 0.694 down to near-ideal 0.528 at minor cost in Macro-F1.
2. Zero Raw Data Exposure: All federated configurations keep client records completely localized on client gateways.
3. Secure Aggregation Zero-Overhead Accuracy: SecAgg achieves 100% exact mathematical equivalence to FedAvg while ensuring the server never inspects individual weights.
