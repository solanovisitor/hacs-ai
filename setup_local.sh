#!/bin/bash
# HACS Local Development Setup Script
# 
# This script sets up HACS services for local development with proper health checks
# and validation at each step.
#
# Prerequisites:
# - Docker and Docker Compose installed
# - UV package manager installed
#
# Usage: ./setup_local.sh [options]
# Options:
#   --with-qdrant    Start Qdrant vector store (optional)
#   --clean          Clean existing containers before starting
#   --verbose        Show detailed output
#   --help           Show this help message
#
# Author: HACS Development Team
# Version: 1.0.0

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="hacs-fresh"
MCP_SERVER_URL="http://localhost:8000"
POSTGRES_PORT="5432"
QDRANT_PORT="6333"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Flags
WITH_QDRANT=false
CLEAN_START=false
VERBOSE=false

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${CYAN}🔧 $1${NC}"
}

show_help() {
    cat << EOF
HACS Local Development Setup Script

This script sets up HACS services for local development with proper health checks
and validation at each step.

Usage: ./setup_local.sh [options]

Options:
  --with-qdrant    Start Qdrant vector store (optional)
  --clean          Clean existing containers before starting
  --verbose        Show detailed output
  --help           Show this help message

Prerequisites:
  - Docker and Docker Compose installed
  - UV package manager installed

Examples:
  ./setup_local.sh                    # Basic setup with PostgreSQL + MCP Server
  ./setup_local.sh --with-qdrant      # Include Qdrant vector store
  ./setup_local.sh --clean            # Clean start (removes existing containers)
  ./setup_local.sh --verbose          # Show detailed output

EOF
}

check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check UV
    if ! command -v uv &> /dev/null; then
        log_error "UV is not installed. Please install UV first."
        echo "Run: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "pyproject.toml" ]] || [[ ! -f "docker-compose.yml" ]]; then
        log_error "Please run this script from the HACS project root directory."
        exit 1
    fi
    
    log_success "All prerequisites met"
    echo "  - Docker: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
    echo "  - Docker Compose: $(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)"
    echo "  - UV: $(uv --version | cut -d' ' -f2)"
}

setup_workspace() {
    log_step "Setting up UV workspace..."
    
    # Check if workspace needs sync
    if $VERBOSE; then
        uv sync --dry-run
    else
        uv sync --dry-run > /dev/null 2>&1
    fi
    
    log_success "Workspace is up-to-date"
}

clean_existing_services() {
    if $CLEAN_START; then
        log_step "Cleaning existing services..."
        
        # Stop and remove containers
        if $VERBOSE; then
            docker-compose --profile with-qdrant down --remove-orphans --volumes
        else
            docker-compose --profile with-qdrant down --remove-orphans --volumes > /dev/null 2>&1
        fi
        
        log_success "Cleaned existing services"
    fi
}

start_postgres() {
    log_step "Starting PostgreSQL database..."
    
    # Start PostgreSQL
    if $VERBOSE; then
        docker-compose up -d postgres
    else
        docker-compose up -d postgres > /dev/null 2>&1
    fi
    
    # Wait for PostgreSQL to be healthy
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 5  # Give PostgreSQL initial time to start
    
    local retries=0
    local max_retries=30
    
    # Increase timeout if we're doing a clean start (initial setup takes longer)
    if $CLEAN_START; then
        max_retries=60
        log_info "Clean start detected - allowing extra time for database initialization..."
    fi
    
    while [[ $retries -lt $max_retries ]]; do
        # Check if PostgreSQL is ready to accept connections
        if docker-compose exec -T postgres pg_isready -U hacs > /dev/null 2>&1; then
            # Also check if container is healthy
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' hacs-postgres 2>/dev/null || echo "unknown")
            if [[ $health_status == "healthy" ]]; then
                break
            fi
        fi
        
        retries=$((retries + 1))
        if [[ $((retries % 5)) -eq 0 ]]; then
            log_info "Still waiting for PostgreSQL... (${retries}/${max_retries})"
        fi
        sleep 2
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "PostgreSQL failed to start within expected time"
        docker-compose logs postgres
        exit 1
    fi
    
    # Verify health status
    local status=$(docker-compose ps postgres --format "table {{.Status}}" | tail -n +2)
    if [[ $status == *"(healthy)"* ]]; then
        log_success "PostgreSQL is healthy and ready"
    else
        log_error "PostgreSQL is not healthy: $status"
        exit 1
    fi
}

start_mcp_server() {
    log_step "Starting HACS MCP Server..."
    
    # Start MCP Server
    if $VERBOSE; then
        docker-compose up -d hacs-mcp-server
    else
        docker-compose up -d hacs-mcp-server > /dev/null 2>&1
    fi
    
    # Wait for MCP server to be ready
    log_info "Waiting for MCP server to initialize..."
    sleep 10  # Give MCP server initial time to start
    
    local retries=0
    local max_retries=30
    
    while [[ $retries -lt $max_retries ]]; do
        if curl -s -X POST "$MCP_SERVER_URL/" \
           -H "Content-Type: application/json" \
           -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' > /dev/null 2>&1; then
            break
        fi
        
        retries=$((retries + 1))
        if [[ $((retries % 5)) -eq 0 ]]; then
            log_info "Still waiting for MCP server... (${retries}/${max_retries})"
        fi
        sleep 2
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "MCP server failed to start within expected time"
        docker-compose logs hacs-mcp-server
        exit 1
    fi
    
    # Verify health status
    local status=$(docker-compose ps hacs-mcp-server --format "table {{.Status}}" | tail -n +2)
    if [[ $status == *"(healthy)"* ]]; then
        log_success "MCP Server is healthy and ready"
    else
        log_error "MCP server is not healthy: $status"
        exit 1
    fi
}

start_qdrant() {
    if $WITH_QDRANT; then
        log_step "Starting Qdrant vector store..."
        
        # Start Qdrant
        if $VERBOSE; then
            docker-compose --profile with-qdrant up -d qdrant
        else
            docker-compose --profile with-qdrant up -d qdrant > /dev/null 2>&1
        fi
        
        # Wait for Qdrant to be ready
        log_info "Waiting for Qdrant to initialize..."
        local retries=0
        local max_retries=20
        
        while [[ $retries -lt $max_retries ]]; do
            if curl -s "http://localhost:$QDRANT_PORT/health" > /dev/null 2>&1; then
                break
            fi
            
            retries=$((retries + 1))
            if [[ $((retries % 5)) -eq 0 ]]; then
                log_info "Still waiting for Qdrant... (${retries}/${max_retries})"
            fi
            sleep 2
        done
        
        if [[ $retries -eq $max_retries ]]; then
            log_warning "Qdrant failed to start within expected time - continuing without vector store"
            log_info "Try running with --clean option to reset Qdrant data"
            docker-compose logs qdrant | tail -10
            return 0  # Don't exit, just continue without Qdrant
        fi
        
        log_success "Qdrant vector store is ready"
    fi
}

verify_setup() {
    log_step "Verifying complete setup..."
    
    # Test MCP server tools list
    local tools_response=$(curl -s -X POST "$MCP_SERVER_URL/" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"tools/list","id":1}')
    
    local tools_count=$(echo "$tools_response" | grep -o '"name"' | wc -l | tr -d ' ')
    
    if [[ $tools_count -gt 0 ]]; then
        log_success "MCP server responding with $tools_count tools available"
    else
        log_error "MCP server not responding correctly"
        echo "Response: $tools_response"
        exit 1
    fi
    
    # Test a basic tool
    log_info "Testing basic tool functionality..."
    local test_response=$(curl -s -X POST "$MCP_SERVER_URL/" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"discover_hacs_resources","arguments":{}},"id":2}')
    
    if echo "$test_response" | grep -q '"result"'; then
        log_success "Basic tool functionality verified"
    else
        log_warning "Basic tool test had issues, but services are running"
    fi
}

show_status() {
    echo ""
    echo "🎉 HACS Local Development Environment Ready!"
    echo "=============================================="
    echo ""
    
    # Service status
    local postgres_status=$(docker-compose ps postgres --format "table {{.Status}}" | tail -n +2)
    local mcp_status=$(docker-compose ps hacs-mcp-server --format "table {{.Status}}" | tail -n +2)
    
    echo "📊 Service Status:"
    if [[ $postgres_status == *"(healthy)"* ]]; then
        echo "  ✅ PostgreSQL: Running (Port: $POSTGRES_PORT)"
    else
        echo "  ❌ PostgreSQL: $postgres_status"
    fi
    
    if [[ $mcp_status == *"(healthy)"* ]]; then
        echo "  ✅ MCP Server: Running (Port: 8000)"
    else
        echo "  ❌ MCP Server: $mcp_status"
    fi
    
    if $WITH_QDRANT; then
        local qdrant_status=$(docker-compose --profile with-qdrant ps qdrant --format "table {{.Status}}" | tail -n +2 2>/dev/null || echo "Not running")
        if [[ $qdrant_status == *"Up"* ]]; then
            # Double check if Qdrant is actually healthy
            if curl -s "http://localhost:$QDRANT_PORT/health" > /dev/null 2>&1; then
                echo "  ✅ Qdrant: Running (Port: $QDRANT_PORT)"
            else
                echo "  ⚠️  Qdrant: Container running but not responding (Port: $QDRANT_PORT)"
            fi
        else
            echo "  ❌ Qdrant: $qdrant_status"
        fi
    fi
    
    echo ""
    echo "🔗 Service URLs:"
    echo "  • MCP Server: $MCP_SERVER_URL"
    echo "  • PostgreSQL: postgresql://hacs:hacs_dev@localhost:$POSTGRES_PORT/hacs"
    if $WITH_QDRANT; then
        echo "  • Qdrant: http://localhost:$QDRANT_PORT"
    fi
    
    echo ""
    echo "🛠️  Quick Commands:"
    echo "  • List tools: curl -X POST $MCP_SERVER_URL/ -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}'"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart services: docker-compose restart"
    
    echo ""
    echo "📚 Next Steps:"
    echo "  1. Run your HACS agent: cd examples/hacs_developer_agent && uv run langgraph dev"
    echo "  2. View the comprehensive testing guide: cat docs/testing.md"
    echo "  3. Test all tools: python tests/test_hacs_tools_comprehensive.py"
    
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-qdrant)
            WITH_QDRANT=true
            shift
            ;;
        --clean)
            CLEAN_START=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "🚀 HACS Local Development Setup"
    echo "==============================="
    
    if $VERBOSE; then
        echo "Configuration:"
        echo "  - Clean start: $CLEAN_START"
        echo "  - Include Qdrant: $WITH_QDRANT"
        echo "  - Verbose output: $VERBOSE"
        echo ""
    fi
    
    check_prerequisites
    setup_workspace
    clean_existing_services
    start_postgres
    start_mcp_server
    start_qdrant
    verify_setup
    show_status
}

# Execute main function
main "$@"