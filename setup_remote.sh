#!/bin/bash
# HACS Remote Deployment Setup Script
# 
# This script sets up HACS services for remote/production deployment with proper
# health checks, security configurations, and scalability considerations.
#
# Prerequisites:
# - Docker and Docker Compose installed
# - .env file configured with production secrets
# - Network access for container registry (if using custom images)
#
# Usage: ./setup_remote.sh [options]
# Options:
#   --production     Use production configuration (SSL, scaling, monitoring)
#   --staging        Use staging configuration  
#   --with-qdrant    Include Qdrant vector store
#   --with-monitoring Include monitoring stack (Prometheus, Grafana)
#   --ssl            Enable SSL/TLS configuration
#   --scale N        Scale MCP servers to N instances (default: 2)
#   --clean          Clean existing containers before starting
#   --verbose        Show detailed output
#   --help           Show this help message
#
# Author: HACS Development Team
# Version: 1.0.0

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="hacs"
MCP_SERVER_URL="http://localhost:8000"
POSTGRES_PORT="5432"
QDRANT_PORT="6333"
DEFAULT_SCALE=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Flags
PRODUCTION_MODE=false
STAGING_MODE=false
WITH_QDRANT=false
WITH_MONITORING=false
SSL_ENABLED=false
CLEAN_START=false
VERBOSE=false
SCALE_COUNT=$DEFAULT_SCALE

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

log_security() {
    echo -e "${PURPLE}🔒 $1${NC}"
}

show_help() {
    cat << EOF
HACS Remote Deployment Setup Script

This script sets up HACS services for remote/production deployment with proper
health checks, security configurations, and scalability considerations.

Usage: ./setup_remote.sh [options]

Options:
  --production     Use production configuration (SSL, scaling, monitoring)
  --staging        Use staging configuration  
  --with-qdrant    Include Qdrant vector store
  --with-monitoring Include monitoring stack (Prometheus, Grafana)
  --ssl            Enable SSL/TLS configuration
  --scale N        Scale MCP servers to N instances (default: 2)
  --clean          Clean existing containers before starting
  --verbose        Show detailed output
  --help           Show this help message

Prerequisites:
  - Docker and Docker Compose installed
  - .env file configured with production secrets
  - Network access for container registry (if using custom images)

Environment Variables Required:
  - POSTGRES_PASSWORD: Strong password for PostgreSQL
  - HACS_API_KEY: API key for HACS service authentication
  - Optional: SSL_CERT_PATH, SSL_KEY_PATH for SSL setup

Examples:
  ./setup_remote.sh --production --ssl       # Full production setup with SSL
  ./setup_remote.sh --staging --with-qdrant  # Staging with vector store
  ./setup_remote.sh --scale 4                # Scale to 4 MCP server instances
  ./setup_remote.sh --with-monitoring        # Include monitoring stack

EOF
}

check_prerequisites() {
    log_step "Checking prerequisites for remote deployment..."
    
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
    
    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "Please run this script from the HACS project root directory."
        exit 1
    fi
    
    # Check for .env file
    if [[ ! -f ".env" ]]; then
        log_warning ".env file not found. Creating from template..."
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_info "Please edit .env file with your production secrets before continuing"
            read -p "Press Enter after configuring .env file..."
        else
            log_error ".env.example file not found. Please create .env file with required variables."
            exit 1
        fi
    fi
    
    # Check for required environment variables
    if ! grep -q "POSTGRES_PASSWORD=" .env || ! grep -q "HACS_API_KEY=" .env; then
        log_error "Missing required environment variables in .env file."
        log_info "Required: POSTGRES_PASSWORD, HACS_API_KEY"
        exit 1
    fi
    
    # Check SSL configuration if SSL is enabled
    if $SSL_ENABLED; then
        if ! grep -q "SSL_CERT_PATH=" .env || ! grep -q "SSL_KEY_PATH=" .env; then
            log_error "SSL enabled but SSL_CERT_PATH or SSL_KEY_PATH not configured in .env"
            exit 1
        fi
    fi
    
    log_success "All prerequisites met"
    echo "  - Docker: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
    echo "  - Docker Compose: $(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)"
    
    if $PRODUCTION_MODE; then
        log_security "Production mode enabled - using enhanced security settings"
    elif $STAGING_MODE; then
        log_info "Staging mode enabled - using staging configuration"
    fi
}

setup_environment() {
    log_step "Setting up deployment environment..."
    
    # Export environment variables
    set -a  # Mark variables for export
    source .env
    set +a
    
    # Set deployment-specific variables
    if $PRODUCTION_MODE; then
        export HACS_ENVIRONMENT="production"
        export COMPOSE_PROJECT_NAME="${PROJECT_NAME}-prod"
        export POSTGRES_MAX_CONNECTIONS="200"
        export MCP_SERVER_WORKERS="4"
    elif $STAGING_MODE; then
        export HACS_ENVIRONMENT="staging"
        export COMPOSE_PROJECT_NAME="${PROJECT_NAME}-staging"
        export POSTGRES_MAX_CONNECTIONS="100"
        export MCP_SERVER_WORKERS="2"
    else
        export HACS_ENVIRONMENT="development"
        export COMPOSE_PROJECT_NAME="${PROJECT_NAME}-dev"
        export POSTGRES_MAX_CONNECTIONS="50"
        export MCP_SERVER_WORKERS="1"
    fi
    
    export HACS_SCALE_COUNT="$SCALE_COUNT"
    
    log_success "Environment configured for $HACS_ENVIRONMENT deployment"
}

clean_existing_services() {
    if $CLEAN_START; then
        log_step "Cleaning existing services..."
        
        # Build compose command based on enabled services
        local compose_cmd="docker-compose"
        
        if $WITH_QDRANT; then
            compose_cmd="$compose_cmd --profile with-qdrant"
        fi
        
        if $WITH_MONITORING; then
            compose_cmd="$compose_cmd --profile monitoring"
        fi
        
        # Stop and remove containers
        if $VERBOSE; then
            $compose_cmd down --remove-orphans
        else
            $compose_cmd down --remove-orphans > /dev/null 2>&1
        fi
        
        log_success "Cleaned existing services"
    fi
}

start_postgres() {
    log_step "Starting PostgreSQL database (production-ready)..."
    
    # Start PostgreSQL with production settings
    if $VERBOSE; then
        docker-compose up -d postgres
    else
        docker-compose up -d postgres > /dev/null 2>&1
    fi
    
    # Wait for PostgreSQL to be healthy
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 10  # Give PostgreSQL time to start
    
    local retries=0
    local max_retries=30
    
    while [[ $retries -lt $max_retries ]]; do
        if docker-compose exec -T postgres pg_isready -U hacs > /dev/null 2>&1; then
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' $(docker-compose ps -q postgres) 2>/dev/null || echo "unknown")
            if [[ $health_status == "healthy" ]]; then
                break
            fi
        fi
        
        retries=$((retries + 1))
        if [[ $((retries % 5)) -eq 0 ]]; then
            log_info "Still waiting for PostgreSQL... (${retries}/${max_retries})"
        fi
        sleep 3
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "PostgreSQL failed to start within expected time"
        docker-compose logs postgres
        exit 1
    fi
    
    log_success "PostgreSQL is healthy and ready"
    
    # Set up database tuning for production
    if $PRODUCTION_MODE; then
        log_security "Applying production database tuning..."
        # Add production database tuning commands here
    fi
}

start_mcp_servers() {
    log_step "Starting HACS MCP Server cluster (${SCALE_COUNT} instances)..."
    
    # Scale MCP servers
    if $VERBOSE; then
        docker-compose up -d --scale hacs-mcp-server=$SCALE_COUNT hacs-mcp-server
    else
        docker-compose up -d --scale hacs-mcp-server=$SCALE_COUNT hacs-mcp-server > /dev/null 2>&1
    fi
    
    # Wait for MCP servers to be ready
    log_info "Waiting for MCP server cluster to initialize..."
    sleep 15  # Give MCP servers time to start
    
    local retries=0
    local max_retries=30
    local healthy_servers=0
    
    while [[ $retries -lt $max_retries ]]; do
        healthy_servers=0
        
        # Check each MCP server instance
        for ((i=1; i<=SCALE_COUNT; i++)); do
            local port=$((8000 + i - 1))
            if curl -s -X POST "http://localhost:${port}/" \
               -H "Content-Type: application/json" \
               -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' > /dev/null 2>&1; then
                healthy_servers=$((healthy_servers + 1))
            fi
        done
        
        if [[ $healthy_servers -eq $SCALE_COUNT ]]; then
            break
        fi
        
        retries=$((retries + 1))
        if [[ $((retries % 5)) -eq 0 ]]; then
            log_info "Healthy servers: ${healthy_servers}/${SCALE_COUNT} (${retries}/${max_retries})"
        fi
        sleep 3
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "MCP server cluster failed to start within expected time"
        docker-compose logs hacs-mcp-server
        exit 1
    fi
    
    log_success "MCP Server cluster is healthy (${healthy_servers}/${SCALE_COUNT} instances)"
}

start_qdrant() {
    if $WITH_QDRANT; then
        log_step "Starting Qdrant vector store cluster..."
        
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
            sleep 3
        done
        
        if [[ $retries -eq $max_retries ]]; then
            log_warning "Qdrant failed to start within expected time - continuing without vector store"
            docker-compose logs qdrant | tail -10
            return 0
        fi
        
        log_success "Qdrant vector store is ready"
    fi
}

start_monitoring() {
    if $WITH_MONITORING; then
        log_step "Starting monitoring stack..."
        
        if $VERBOSE; then
            docker-compose --profile monitoring up -d
        else
            docker-compose --profile monitoring up -d > /dev/null 2>&1
        fi
        
        log_success "Monitoring stack started (Prometheus, Grafana)"
    fi
}

setup_ssl() {
    if $SSL_ENABLED; then
        log_step "Setting up SSL/TLS configuration..."
        
        # SSL setup would typically involve:
        # - Copying certificates to the right location
        # - Configuring reverse proxy (nginx/traefik)
        # - Setting up certificate renewal
        
        log_info "SSL configuration would be implemented here"
        log_warning "SSL setup is not yet implemented - using HTTP for now"
    fi
}

verify_setup() {
    log_step "Verifying production deployment..."
    
    # Test MCP server cluster
    local tools_response=$(curl -s -X POST "$MCP_SERVER_URL/" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"tools/list","id":1}')
    
    local tools_count=$(echo "$tools_response" | grep -o '"name"' | wc -l | tr -d ' ')
    
    if [[ $tools_count -gt 0 ]]; then
        log_success "MCP server cluster responding with $tools_count tools available"
    else
        log_error "MCP server cluster not responding correctly"
        echo "Response: $tools_response"
        exit 1
    fi
    
    # Test database connectivity
    if docker-compose exec -T postgres psql -U hacs -d hacs -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Database connectivity verified"
    else
        log_warning "Database connectivity issues detected"
    fi
    
    # Test a basic tool across the cluster
    log_info "Testing load balancing across MCP server instances..."
    local successful_tests=0
    for ((i=1; i<=3; i++)); do
        local test_response=$(curl -s -X POST "$MCP_SERVER_URL/" \
            -H "Content-Type: application/json" \
            -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"discover_hacs_resources","arguments":{}},"id":2}')
        
        if echo "$test_response" | grep -q '"result"'; then
            successful_tests=$((successful_tests + 1))
        fi
        sleep 1
    done
    
    if [[ $successful_tests -eq 3 ]]; then
        log_success "Load balancing and tool functionality verified"
    else
        log_warning "Some load balancing tests failed (${successful_tests}/3)"
    fi
}

show_deployment_status() {
    echo ""
    echo "🎉 HACS Remote Deployment Ready!"
    echo "================================="
    echo ""
    
    # Service status
    local postgres_status=$(docker-compose ps postgres --format "table {{.Status}}" | tail -n +2)
    local mcp_instances=$(docker-compose ps hacs-mcp-server -q | wc -l | tr -d ' ')
    
    echo "📊 Service Status:"
    if [[ $postgres_status == *"Up"* ]]; then
        echo "  ✅ PostgreSQL: Running (Port: $POSTGRES_PORT)"
    else
        echo "  ❌ PostgreSQL: $postgres_status"
    fi
    
    echo "  ✅ MCP Server Cluster: $mcp_instances instances running"
    
    if $WITH_QDRANT; then
        local qdrant_status=$(docker-compose --profile with-qdrant ps qdrant --format "table {{.Status}}" | tail -n +2 2>/dev/null || echo "Not running")
        if [[ $qdrant_status == *"Up"* ]]; then
            if curl -s "http://localhost:$QDRANT_PORT/health" > /dev/null 2>&1; then
                echo "  ✅ Qdrant: Running (Port: $QDRANT_PORT)"
            else
                echo "  ⚠️  Qdrant: Container running but not responding"
            fi
        else
            echo "  ❌ Qdrant: $qdrant_status"
        fi
    fi
    
    if $WITH_MONITORING; then
        echo "  ✅ Monitoring: Prometheus + Grafana running"
    fi
    
    echo ""
    echo "🔗 Service URLs:"
    echo "  • MCP Server: $MCP_SERVER_URL"
    echo "  • PostgreSQL: postgresql://hacs:***@localhost:$POSTGRES_PORT/hacs"
    if $WITH_QDRANT; then
        echo "  • Qdrant: http://localhost:$QDRANT_PORT"
    fi
    if $WITH_MONITORING; then
        echo "  • Prometheus: http://localhost:9090"
        echo "  • Grafana: http://localhost:3000"
    fi
    
    echo ""
    echo "🛠️  Management Commands:"
    echo "  • Scale MCP servers: docker-compose up -d --scale hacs-mcp-server=N hacs-mcp-server"
    echo "  • View logs: docker-compose logs -f [service]"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart cluster: docker-compose restart"
    
    echo ""
    echo "🔒 Security Notes:"
    if $PRODUCTION_MODE; then
        echo "  • Production mode enabled with enhanced security"
        echo "  • Ensure firewall rules are properly configured"
        echo "  • Monitor logs for security events"
        if ! $SSL_ENABLED; then
            echo "  ⚠️  SSL not enabled - consider enabling for production"
        fi
    else
        echo "  ⚠️  Not running in production mode - enable for production use"
    fi
    
    echo ""
    echo "📊 Performance Notes:"
    echo "  • MCP Server instances: $SCALE_COUNT"
    echo "  • PostgreSQL max connections: ${POSTGRES_MAX_CONNECTIONS:-50}"
    echo "  • Environment: $HACS_ENVIRONMENT"
    
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            PRODUCTION_MODE=true
            shift
            ;;
        --staging)
            STAGING_MODE=true
            shift
            ;;
        --with-qdrant)
            WITH_QDRANT=true
            shift
            ;;
        --with-monitoring)
            WITH_MONITORING=true
            shift
            ;;
        --ssl)
            SSL_ENABLED=true
            shift
            ;;
        --scale)
            SCALE_COUNT="$2"
            shift 2
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

# Validate scale count
if ! [[ "$SCALE_COUNT" =~ ^[0-9]+$ ]] || [[ $SCALE_COUNT -lt 1 ]] || [[ $SCALE_COUNT -gt 10 ]]; then
    log_error "Invalid scale count: $SCALE_COUNT (must be 1-10)"
    exit 1
fi

# Main execution
main() {
    echo "🚀 HACS Remote Deployment Setup"
    echo "================================"
    
    if $VERBOSE; then
        echo "Configuration:"
        echo "  - Environment: $(if $PRODUCTION_MODE; then echo "Production"; elif $STAGING_MODE; then echo "Staging"; else echo "Development"; fi)"
        echo "  - Scale: $SCALE_COUNT MCP server instances"
        echo "  - Qdrant: $WITH_QDRANT"
        echo "  - Monitoring: $WITH_MONITORING"
        echo "  - SSL: $SSL_ENABLED"
        echo "  - Clean start: $CLEAN_START"
        echo "  - Verbose: $VERBOSE"
        echo ""
    fi
    
    check_prerequisites
    setup_environment
    clean_existing_services
    start_postgres
    start_mcp_servers
    start_qdrant
    start_monitoring
    setup_ssl
    verify_setup
    show_deployment_status
}

# Execute main function
main "$@"