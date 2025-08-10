#!/bin/bash

# HACS Test Runner Script
# Provides local and docker-based testing options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        return 1
    fi
    
    return 0
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed or not in PATH"
        return 1
    fi
    return 0
}

# Function to run local tests
run_local_tests() {
    print_status "Running local tests..."
    
    # Check if UV is available
    if ! command -v uv &> /dev/null; then
        print_error "UV package manager is not installed. Please install UV first."
        print_status "Install UV with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    # Install dependencies with UV if needed
    if ! python3 -c "import pytest" 2>/dev/null; then
        print_warning "pytest not available, installing with UV..."
        uv pip install pytest pytest-asyncio
    fi
    
    # Set Python path to include packages
    export PYTHONPATH="$PWD/packages/hacs-models/src:$PWD/packages/hacs-core/src:$PWD/packages/hacs-tools/src:$PWD/packages/hacs-auth/src:$PWD/packages/hacs-persistence/src:$PWD/packages/hacs-registry/src:$PWD/packages/hacs-utils/src:$PWD/packages/hacs-infrastructure/src:$PYTHONPATH"
    
    # Run specific test categories
    case "${1:-all}" in
        "unit")
            print_status "Running unit tests..."
            python3 -m pytest tests/test_ci_essential.py -v
            ;;
        "integration")
            print_status "Running integration tests..."
            python3 -m pytest tests/test_phase2_integration.py -v
            ;;
        "phase2")
            print_status "Running Phase 2 integration tests..."
            python3 -m pytest tests/test_phase2_integration.py -v --tb=short
            ;;
        "all"|*)
            print_status "Running all available tests..."
            python3 -m pytest tests/ -v --tb=short
            ;;
    esac
}

# Function to run docker tests
run_docker_tests() {
    print_status "Running tests in Docker environment..."
    
    if ! check_docker || ! check_docker_compose; then
        print_error "Docker environment not available"
        return 1
    fi
    
    # Build and run test environment
    print_status "Building Docker test environment..."
    docker-compose --profile test build
    
    print_status "Starting test services..."
    docker-compose --profile test up -d postgres qdrant
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Run tests
    print_status "Executing tests..."
    docker-compose --profile test run --rm test-runner
    
    # Cleanup
    print_status "Cleaning up test environment..."
    docker-compose --profile test down
}

# Function to validate environment
validate_environment() {
    print_status "Validating HACS environment..."
    
    # Check required files
    local required_files=(
        "docker-compose.yml"
        "pyproject.toml"
        "packages/hacs-models/pyproject.toml"
        "packages/hacs-tools/pyproject.toml"
        "tests/test_ci_essential.py"
        "tests/test_phase2_integration.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "Required file missing: $file"
            return 1
        fi
    done
    
    # Check package structure
    local packages=(
        "hacs-models"
        "hacs-core" 
        "hacs-tools"
        "hacs-auth"
        "hacs-persistence"
        "hacs-registry"
        "hacs-utils"
    )
    
    for package in "${packages[@]}"; do
        if [[ ! -d "packages/$package/src" ]]; then
            print_error "Package source missing: packages/$package/src"
            return 1
        fi
    done
    
    # Test basic imports
    export PYTHONPATH="$PWD/packages/hacs-models/src:$PWD/packages/hacs-core/src:$PYTHONPATH"
    
    if python3 -c "from hacs_models import Patient, MemoryBlock, Actor; print('✓ Core models import successful')" 2>/dev/null; then
        print_success "Core model imports working"
    else
        print_warning "Core model imports have issues (may need package installation)"
    fi
    
    print_success "Environment validation completed"
}

# Function to show usage
show_usage() {
    echo "HACS Test Runner"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  local [unit|integration|phase2|all]  Run tests locally"
    echo "  docker                               Run tests in Docker environment"
    echo "  validate                             Validate environment setup"
    echo "  help                                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local unit                        Run local unit tests"
    echo "  $0 local phase2                      Run Phase 2 integration tests"
    echo "  $0 docker                            Run full Docker test suite"
    echo "  $0 validate                          Check environment setup"
    echo ""
    echo "Prerequisites:"
    echo "  UV package manager:                  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Environment Variables (in .env file):"
    echo "  DATABASE_URL                         PostgreSQL connection URL"
    echo "  DB_PASSWORD                          Database password"
    echo "  QDRANT_URL                          Qdrant vector store URL"
    echo "  OPENAI_API_KEY                      OpenAI API key"
    echo "  ANTHROPIC_API_KEY                   Anthropic API key"
    echo "  PINECONE_API_KEY                    Pinecone API key"
    echo ""
}

# Main execution
case "${1:-help}" in
    "local")
        validate_environment
        run_local_tests "$2"
        ;;
    "docker")
        validate_environment
        run_docker_tests
        ;;
    "validate")
        validate_environment
        ;;
    "help"|*)
        show_usage
        ;;
esac
