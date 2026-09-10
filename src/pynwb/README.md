## ndx_hed extension for NWB

This is an NWB extension for adding Hierarchical Event Descriptor (HED) tags to NWB data.
The project README at the repository root has the full description, examples, and links.

This extension was developed by Kay Robbins, Ryan Ly, Oliver Rübel, and the HED Working Group.

## Installation
Python:
```bash
pip install -U ndx-hed
```

## Developer installation
In a Python 3.10-3.14 environment:
```bash
pip install -e ".[dev]" -c constraints/pinned.txt
```

Run tests:
```bash
pytest
```

Style and other checks:
```bash
ruff check .
ruff format --check .
typos .
```
