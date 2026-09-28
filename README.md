# AV Configuration Integrity Checker

A PowerShell utility that detects changes to a fictional AV
configuration using a SHA-256 baseline.

## Purpose

AV troubleshooting often involves determining whether a
configuration has changed. This project demonstrates a basic
file-integrity check with repeatable tests and JSON reporting.

## Features

- Records an original configuration fingerprint.
- Detects changes to file contents.
- Identifies a missing configuration file.
- Saves timestamped results in JSON.
- Prevents accidental replacement of an existing baseline.

## Technologies and Skills

PowerShell, functions, parameters, conditional logic, file handling,
SHA-256 hashing, JSON processing, and troubleshooting.

## Running the Tool

Open PowerShell in the project folder.

Create a baseline once:

    .\integrity-check.ps1 -Mode Baseline

Check the configuration:

    .\integrity-check.ps1 -Mode Check

The script must be permitted by the computer's execution policy.

## Verified Tests

| Test | Expected result | Observed result |
| --- | --- | --- |
| Original configuration | PASS | PASS |
| Microphone gain changed to -10 | CHANGED | CHANGED |
| Exact original file restored | PASS | PASS |
| Configuration temporarily renamed | MISSING | MISSING |
| Original filename restored | PASS | PASS |

## Files

- integrity-check.ps1: Main program.
- demo-config.json: Fictional AV configuration.
- baseline.json: Original SHA-256 fingerprint.
- original-config.json: Exact restoration copy.
- last-check.json: Latest check result.
- evidence-pass.json: Unchanged-file test evidence.
- evidence-changed.json: Changed-file test evidence.
- evidence-missing.json: Missing-file test evidence.

## Limitations

The checker compares file bytes. Formatting changes can trigger
CHANGED even when the configuration's meaning is unchanged.

It does not identify which setting changed or determine whether
a change was authorized.

The baseline must be trusted and protected. Someone who can
modify both the configuration and baseline can defeat the check.

This version checks one file and uses fictional data.

## Troubleshooting Experience

During setup, I resolved Windows and Linux path confusion,
PowerShell command-entry issues, and a downloaded-file marker
that prevented the practice script from running under RemoteSigned.

## Future Improvements

- Check multiple configuration files.
- Detect added and deleted files.
- Generate an HTML report.
- Add automated tests.

## Version 2 — Configuration Field Comparison

The checker now records both a SHA-256 hash and the original
configuration settings in baseline-v2.json.

It identifies:
- Modified settings, including old and new values.
- Added settings and their values.
- Removed settings and their previous values.

Example output:

    CHANGED : Configuration settings differ from the baseline.
      displayInput: "HDMI1" -> "HDMI2"
      microphoneGainDb: 0 -> -10

### Verified Version 2 Tests

| Test | Observed result |
| --- | --- |
| Modified microphone gain and display input | Both changes identified |
| Added projectorPower | ADDED with value "On" |
| Removed displayInput | REMOVED with previous value "HDMI1" |
| Restored the exact original configuration | PASS |

### Version 2 Files

- baseline-v2.json: Hash and original configuration settings.
- original-config-v2.json: Exact restoration copy.
- evidence-v2-modified.json: Modified-field test result.
- evidence-v2-added.json: Added-field test result.
- evidence-v2-removed.json: Removed-field test result.

The script now uses baseline-v2.json. The earlier baseline.json
is retained from version 1.

### Comparison Scope

Field comparison operates at the top level of the JSON object.
Nested structures are compared as whole values.

File formatting changes still trigger CHANGED when the byte-level
hash differs, even if the top-level setting values match.

The baseline must remain trusted and protected.