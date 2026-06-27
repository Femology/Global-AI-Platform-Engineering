# 🔍 RepoLens: Privacy-First Offline Architecture Analyzer

RepoLens is a high-utility developer tool designed to map code structure and verify architectural boundaries using Python's native **Abstract Syntax Tree (AST)**. Unlike generic AI coding tools that upload your raw, proprietary source code to external cloud platforms, RepoLens analyzes your structural syntax blueprints completely offline—retaining absolute code privacy.

---

## 🚀 Key Features

* **Deterministic Offline Analysis:** Operates entirely locally on your machine. Your proprietary intellectual property never traverses external networks.
* **Abstract Syntax Tree (AST) Inspection:** Maps class hierarchies, function signatures, module dependencies, and docstrings from the logical blueprint of your code, completely avoiding rough regex-based string matching guesses.
* **Clean Architecture Verification:** Evaluates structural dependency rules automatically to prevent low-level infrastructure leaking directly into high-level pure domain models.
* **Developer Onboarding Mapping:** Automatically transforms a dense, unfamiliar repository into a scannable structural summary for immediate project understanding.

---

## 🛠️ Project Structure

```text
Global-AI-Platform-Engineering/
├── src/
│   └── repolens/
│       └── infrastructure/
│           └── parsers.py     <- Core deterministic AST analysis logic
├── nexus.py                   <- Interface manager and CLI utility runner
├── pyproject.toml             <- Python package configuration
└── requirements.txt           <- Standard dependency listings
