# Contributing to HACS: Healthcare Agent Communication Standard

Welcome to the HACS community! We're building the definitive platform for healthcare AI agent communication, and your contribution makes a difference in advancing healthcare technology globally.

## 🏥 **About HACS**

HACS (Healthcare Agent Communication Standard) is a production-ready platform enabling healthcare organizations to deploy AI agents with structured memory, clinical reasoning, and FHIR compliance. Built on the Model Context Protocol (MCP), HACS provides 25+ specialized Hacs Tools for patient data management, clinical workflows, and evidence-based reasoning.

## 🚀 **Quick Start for Contributors**

### **Prerequisites**
- Python 3.11+
- [UV](https://github.com/astral-sh/uv) - Fast Python package manager
- Git and GitHub account
- Docker & Docker Compose (for full development)

### **1. Fork and Clone**
```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR-USERNAME/hacs-ai.git
cd hacs-ai

# Add upstream remote for staying in sync
git remote add upstream https://github.com/solanovisitor/hacs-ai.git
```

### **2. Development Environment Setup**
```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync UV workspace (installs all HACS packages in development mode)
uv sync

# Activate the development environment
source .venv/bin/activate

# Verify installation
uv run python -c "import hacs_core; print('✅ HACS development environment ready!')"
```

### **3. Start Development Services**
```bash
# Start PostgreSQL + pgvector and MCP server
docker-compose up -d

# Verify services are running
curl http://localhost:8000/  # MCP server health check
```

### **4. Run Tests**
```bash
# Run essential tests to ensure everything works
uv run pytest tests/test_ci_essential.py -v

# Run all tests
uv run pytest

# Run specific package tests
uv run pytest tests/test_hacs_core_unit.py
```

## 🌳 **Branch Strategy & Workflow**

We use a **GitFlow-inspired** branching strategy optimized for healthcare AI development:

### **Branch Types**

#### **🚀 Production Branches**
- **`main`** - Production-ready code, always deployable
- **`release/v*`** - Release preparation and stabilization

#### **🔬 Development Branches**  
- **`develop`** - Integration branch for features
- **`feature/*`** - New features and enhancements
- **`experimental/*`** - Research and experimental features

#### **🏥 Healthcare-Specific Branches**
- **`clinical/*`** - Clinical workflow implementations
- **`fhir/*`** - FHIR standard updates and compliance
- **`security/*`** - Healthcare security and compliance features

#### **🛠️ Maintenance Branches**
- **`bugfix/*`** - Bug fixes for develop branch
- **`hotfix/*`** - Critical fixes for production
- **`docs/*`** - Documentation improvements

#### **🧪 Testing & Quality**
- **`test/*`** - Test improvements and new test suites
- **`performance/*`** - Performance optimizations
- **`refactor/*`** - Code refactoring without feature changes

### **Workflow Process**

#### **For New Features:**
```bash
# 1. Create feature branch from develop
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name

# 2. Develop and test
# ... make your changes ...
uv run pytest
uv run ruff check packages/

# 3. Push and create PR to develop
git push origin feature/your-feature-name
# Open PR: feature/your-feature-name → develop
```

#### **For Bug Fixes:**
```bash
# 1. Create bugfix branch from develop  
git checkout develop
git pull upstream develop
git checkout -b bugfix/issue-description

# 2. Fix and test
# ... make your changes ...
uv run pytest tests/test_ci_essential.py

# 3. Push and create PR to develop
git push origin bugfix/issue-description
```

#### **For Hotfixes:**
```bash
# 1. Create hotfix branch from main
git checkout main
git pull upstream main
git checkout -b hotfix/critical-fix

# 2. Fix and test thoroughly
# ... make your changes ...
uv run pytest

# 3. Create PRs to both main AND develop
git push origin hotfix/critical-fix
# Open PR: hotfix/critical-fix → main
# Open PR: hotfix/critical-fix → develop
```

## 📦 **Development Guidelines**

### **Code Quality Standards**
```bash
# Before committing, always run:
uv run ruff check packages/ --fix    # Code formatting and linting
uv run pytest tests/test_ci_essential.py  # Essential functionality
uv run python publish.py --check    # Package validation
```

### **Package Development**
Our UV workspace contains focused packages:

- **`hacs-core`** - Core models, actors, memory, evidence
- **`hacs-tools`** - 25+ Hacs Tools for AI agents  
- **`hacs-utils`** - Integrations, MCP server, adapters
- **`hacs-persistence`** - Database adapters and migrations
- **`hacs-registry`** - Model and workflow definitions
- **`hacs-cli`** - Command-line interface

#### **Adding Dependencies**
```bash
# Add to specific package
cd packages/hacs-core
uv add pydantic

# Add development dependency to workspace
uv add --dev pytest-cov

# Add optional dependency
uv add --optional anthropic
```

#### **Testing New Packages**
```bash
# Test specific package
uv run pytest packages/hacs-core/

# Test package builds
uv build --package hacs-core

# Test package installation
uv run pip install dist/hacs_core-*.whl
```

### **Healthcare-Specific Guidelines**

#### **🏥 Clinical Data Handling**
- Always use FHIR-compliant data models
- Implement proper validation for healthcare data
- Follow HIPAA guidelines for data processing
- Use Actor-based permissions for access control

#### **🔐 Security Requirements**
- Never commit API keys or credentials
- Use environment variables for sensitive config
- Implement audit logging for all operations
- Follow healthcare data security standards

#### **📋 FHIR Compliance**
- Validate against FHIR R4 standards
- Use proper resource types and fields
- Implement proper error handling
- Test with real FHIR data when possible

## 🧪 **Testing Guidelines**

### **Test Categories**
```bash
# Essential tests (must always pass)
uv run pytest tests/test_ci_essential.py

# Unit tests by package
uv run pytest tests/test_hacs_core_unit.py
uv run pytest tests/test_hacs_tools_unit.py

# Integration tests
uv run pytest packages/hacs-utils/test_integrations_basic.py

# Performance tests
uv run pytest tests/ -m performance
```

### **Writing Tests**
- **Healthcare data**: Use realistic but anonymized test data
- **Edge cases**: Test with invalid FHIR resources
- **Error handling**: Verify graceful degradation
- **Performance**: Test with large datasets when relevant

## 📚 **Documentation Standards**

### **Code Documentation**
- Usedocstrings for all public functions
- Include healthcare context and FHIR compliance notes
- Provide usage examples with clinical scenarios
- Document security and privacy considerations

### **API Documentation**
- Document all tool parameters and return types
- Include clinical workflow examples
- Specify FHIR resource requirements
- Note healthcare compliance requirements

## 🚀 **Release Process**

### **Preparing a Release**
```bash
# 1. Create release branch
git checkout develop
git checkout -b release/v1.2.0

# 2. Update version numbers
# Edit pyproject.toml files for all packages

# 3. Run full test suite
uv run pytest
uv run python publish.py --check

# 4. Test publishing to TestPyPI
uv run python publish.py --test

# 5. Create PR to main
# Open PR: release/v1.2.0 → main
```

### **Publishing Process**
1. Merge release branch to `main`
2. Tag the release: `git tag v1.2.0`
3. Publish to PyPI: `uv run python publish.py --production`
4. Merge back to `develop`
5. Create GitHub release with notes

## 🏆 **Recognition & Community**

### **Contributor Recognition**
- Contributors are acknowledged in release notes
- Significant contributions earn co-author recognition
- Healthcare professionals receive special recognition
- Open source contributions can include professional references

### **Types of Contributions We Value**
- 🏥 **Clinical Expertise**: Healthcare workflow improvements
- 💻 **Technical Development**: Core platform enhancements  
- 📚 **Documentation**: Clear,guides
- 🧪 **Testing**: Robust test coverage and quality assurance
- 🔐 **Security**: Healthcare compliance and data protection
- 🌍 **Community**: Helping other contributors and users

## 📞 **Getting Help**

### **Communication Channels**
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Community Q&A and announcements
- **Pull Request Reviews**: Code discussion and feedback

### **Mentorship Program**
- New contributors get paired with experienced maintainers
- Healthcare professionals receive technical mentoring
- Developers receive clinical context and healthcare guidance

## 📄 **License & Legal**

By contributing to HACS, you agree that your contributions will be licensed under the MIT License. All contributions must:

- Be your original work or properly attributed
- Not violate any third-party copyrights or patents
- Comply with healthcare data protection regulations
- Follow open source contribution best practices

---

## 🎯 **Ready to Contribute?**

1. **🍴 Fork** the repository
2. **🌿 Create** a branch following our strategy
3. **💻 Develop** following our healthcare guidelines  
4. **🧪 Test** thoroughly with clinical scenarios
5. **📝 Document** with healthcare context
6. **🚀 Submit** a pull request

**Together, we're building the future of healthcare AI communication! 🏥✨**

---

*For questions about contributing, please open a GitHub Discussion or reach out to the maintainers. We're here to help you make a meaningful impact on healthcare technology.*