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

- Compare individual JSON fields.
- Check multiple configuration files.
- Detect added and deleted files.
- Generate an HTML report.
- Add automated tests.