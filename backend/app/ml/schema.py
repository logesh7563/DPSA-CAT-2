"""
Fixed Feature Schema and Domain Taxonomy for Federated Preprocessing
Guarantees identical 122-dimensional input feature vectors across all clients without data pooling.
"""

from typing import Dict, List

CLASS_NAMES = ["Normal", "DoS", "Probe", "R2L", "U2R"]
NUM_CLASSES = 5

ATTACK_CATEGORIES = {
    "normal": 0,
    "dos": 1,
    "probe": 2,
    "r2l": 3,
    "u2r": 4
}

ATTACK_NAME_TO_MACRO = {
    "normal": "normal",
    # DoS
    "back": "dos", "land": "dos", "neptune": "dos", "pod": "dos", "smurf": "dos",
    "teardrop": "dos", "mailbomb": "dos", "apache2": "dos", "processtable": "dos",
    "udpstorm": "dos", "snmpgetattack": "dos",
    # Probe
    "ipsweep": "probe", "nmap": "probe", "portsweep": "probe", "satan": "probe",
    "mscan": "probe", "saint": "probe",
    # R2L
    "ftp_write": "r2l", "guess_passwd": "r2l", "imap": "r2l", "multihop": "r2l",
    "phf": "r2l", "spy": "r2l", "warezclient": "r2l", "warezmaster": "r2l",
    "sendmail": "r2l", "named": "r2l", "snmpguess": "r2l", "worm": "r2l",
    "xlock": "r2l", "xsnoop": "r2l", "httptunnel": "r2l",
    # U2R
    "buffer_overflow": "u2r", "loadmodule": "u2r", "perl": "u2r", "rootkit": "u2r",
    "ps": "u2r", "sqlattack": "u2r", "xterm": "u2r"
}

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

TOTAL_FEATURE_DIM = len(FIXED_CATEGORIES["protocol_type"]) + len(FIXED_CATEGORIES["service"]) + len(FIXED_CATEGORIES["flag"]) + len(NUMERICAL_FEATURES)
assert TOTAL_FEATURE_DIM == 122, f"Expected 122 features, got {TOTAL_FEATURE_DIM}"

# Build deterministic list of 122 column names
FEATURE_NAMES: List[str] = []
for col, cats in FIXED_CATEGORIES.items():
    for cat in cats:
        FEATURE_NAMES.append(f"{col}_{cat}")
FEATURE_NAMES.extend(NUMERICAL_FEATURES)
