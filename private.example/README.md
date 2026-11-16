# Private Data Directory (Template)

This directory is a template demonstrating how your personal data should be structured.

## Setup Instructions:
1. Copy this entire folder to `private/`:
   ```bash
   cp -r private.example private
   # On Windows PowerShell:
   Copy-Item -Recurse private.example private
   ```
2. Replace `private/profile.yaml`, `private/cv.md`, and files in `private/writing_samples/` with your genuine personal details and writing style.
3. If using Gmail API later, place your OAuth client secret file at `private/credentials.json`.

> **SECURITY NOTE**: The `private/` directory is strictly ignored by `.git` and will never be committed to Git. The pre-commit hook also blocks any commits attempting to stage files from `private/`.
