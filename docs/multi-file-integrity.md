# AV Integrity Lab — Version 3: multi-file semantic integrity

Adds a Python standard-library **Mac/Linux/Windows** companion to the existing PowerShell checker. This does not replace the original v1/v2 artifacts.

## Run on your Mac

```bash
cd ~/Projects/AV-Integrity-Lab-20260926-175340
python3 -m unittest discover -s tests -v
python3 integrity_multi.py baseline
python3 integrity_multi.py check
```

The example scope includes the fictional original `demo-config.json` and two new fictional AV device files in `lab-fixtures/`.

Unlike byte-level comparison, whitespace-only edits or JSON key reordering will **not** trigger false alarms. Nested keys and array elements are compared semantically; added/removed JSON files in declared directories are flagged. Reports contain changed **paths only**, not secret values.

Output is saved to ignored `reports/` files. Exit codes: **0** for PASS / BASELINED, **1** for CHANGED, **2** for an invalid scope, unsafe path, or missing baseline. Existing baselines are protected against accidental overwrite.

**Portfolio boundary:** these are entirely synthetic fixtures. Do not put operational customer/device configs, passwords, IP schedules, or sensitive data into public GitHub. The tool reports drift, not authorization or malicious intent; baseline tampering remains a threat.

## Follow-up

Integrate the version 3 JSON report into the AV Portfolio Suite dashboard as a clearly labeled lab simulation. Keep your original PowerShell tests and their proven evidence separate.
