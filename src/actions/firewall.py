from __future__ import annotations
import logging
import subprocess
import sys
from ipaddress import ip_address

log = logging.getLogger(__name__)

def run(cmd: list[str]) -> None:
    log.debug("RUN: %s", ' '.join(cmd))
    subprocess.run(cmd, check=True)

def block_ip(ip: str) -> None:
    try:
        ip_address(ip)
    except ValueError:
        log.error("Invalid IP: %s", ip)
        return
    if sys.platform.startswith("linux"):
        cmd = ["sudo", "iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"]
        run(cmd)
        log.info("Blocked %s via iptables", ip)
    elif sys.platform == "darwin":
        rule = f"block drop from {ip} to any"
        anchor = "/etc/pf.anchors/com.anomaly"
        with open(anchor, "a") as f:
            f.write(rule + "\n")
        run(["sudo", "pfctl", "-f", "/etc/pf.conf"])
        log.info("Blocked %s via pfctl", ip)
    else:
        log.warning("Firewall unsupported for %s", sys.platform)