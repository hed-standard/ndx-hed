## ndx_hed Extension for NWB

This is an NWB extension for adding Hierarchical Event Descriptor (HED) tags to NWB data.
HED is a system for

The latest version is 0.2.0. This is the first release of ndx-hed.


This extension was developed by Kay Robbins, Ryan Ly, Oliver Rübel, and the HED Working Group.

## Installation
Python:
```bash
pip install -U ndx-hed
```

## Developer installation
In a Python 3.10-3.14 environment:
```bash
pip install -r requirements-dev.txt
pip install -e .
```

Run tests:
```bash
pytest
```

Install pre-commit hooks:
```bash
pre-commit install
```

Style and other checks:
```bash
black .
ruff .
codespell .
```
