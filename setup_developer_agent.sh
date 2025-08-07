#!/bin/bash

# HACS LangGraph Agent Setup Script
# This script sets up the complete HACS environment with MCP server and LangGraph agents

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

log_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo "$(printf '=%.0s' {1..60})"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Wait for service to be healthy
wait_for_service() {
    local service=$1
    local max_attempts=${2:-30}
    local attempt=0
    
    log_info "Waiting for $service to be healthy..."
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy"; then
            log_success "$service is healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    log_error "$service failed to become healthy after $((max_attempts * 2)) seconds"
    return 1
}

# Test HTTP endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local max_attempts=${3:-15}
    local attempt=0
    
    log_info "Testing $description at $url..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
            log_success "$description is responding"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    log_error "$description is not responding after $((max_attempts * 2)) seconds"
    return 1
}

# Main setup function
main() {
    log_section "🏥 HACS LangGraph Agent Complete Setup"
    
    # Check prerequisites
    log_section "📋 Checking Prerequisites"
    
    local missing_deps=()
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command_exists uv; then
        missing_deps+=("uv")
    fi
    
    if ! command_exists curl; then
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        echo "Please install the missing dependencies and run this script again."
        echo ""
        echo "Installation instructions:"
        echo "- Docker: https://docs.docker.com/get-docker/"
        echo "- UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "- curl: Usually pre-installed or available via package manager"
        exit 1
    fi
    
    log_success "All prerequisites are installed"
    
    # Verify we're in the correct directory
    if [ ! -f "pyproject.toml" ] || [ ! -d "packages" ]; then
        log_error "This script must be run from the HACS root directory"
        log_info "Current directory: $(pwd)"
        log_info "Expected files: pyproject.toml, packages/ directory"
        exit 1
    fi
    
    log_success "Running from correct directory: $(pwd)"
    
    # Step 1: Create required directories and files
    log_section "📁 Setting Up Required Files"
    
    # Create scripts directory if it doesn't exist
    if [ ! -d "scripts" ]; then
        mkdir -p scripts
        log_success "Created scripts directory"
    fi
    
    # Create database initialization script
    cat > scripts/init-db.sql << 'EOF'
-- HACS Database Initialization Script
-- This script sets up the basic database structure for HACS

-- Enable the pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create basic HACS schema
CREATE SCHEMA IF NOT EXISTS hacs;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON SCHEMA hacs TO hacs;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hacs TO hacs;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hacs TO hacs;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA hacs GRANT ALL ON TABLES TO hacs;
ALTER DEFAULT PRIVILEGES IN SCHEMA hacs GRANT ALL ON SEQUENCES TO hacs;

-- Log successful initialization
\echo 'HACS database initialized successfully with pgvector extension';
EOF
    
    log_success "Created database initialization script"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# HACS Environment Configuration

# Database Configuration
POSTGRES_PASSWORD=hacs_dev
DATABASE_URL=postgresql://hacs:hacs_dev@postgres:5432/hacs

# LLM Provider API Keys (add your keys here)
# ANTHROPIC_API_KEY=your_anthropic_key_here
# OPENAI_API_KEY=your_openai_key_here

# Vector Store Configuration
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# HACS Configuration
HACS_API_KEY=dev_key_123
HACS_ENVIRONMENT=development
HACS_MCP_SERVER_URL=http://localhost:8000

# Performance Settings
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
EOF
        log_success "Created .env configuration file"
        log_warning "Please add your API keys to .env file for full functionality"
    else
        log_info ".env file already exists"
    fi
    
    # Step 2: Install Python dependencies
    log_section "📦 Installing Python Dependencies"
    
    log_info "Installing HACS packages with UV..."
    if uv sync --all-extras; then
        log_success "Python dependencies installed successfully"
    else
        log_error "Failed to install Python dependencies"
        exit 1
    fi
    
    # Step 3: Start Docker services
    log_section "🐳 Starting Docker Services"
    
    # Stop any running services first
    log_info "Stopping any existing services..."
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Start PostgreSQL database
    log_info "Starting PostgreSQL database..."
    if docker-compose up -d postgres; then
        log_success "PostgreSQL container started"
    else
        log_error "Failed to start PostgreSQL"
        exit 1
    fi
    
    # Wait for PostgreSQL to be healthy
    if ! wait_for_service postgres 30; then
        log_error "PostgreSQL failed to start properly"
        docker-compose logs postgres
        exit 1
    fi
    
    # Build and start HACS MCP server
    log_info "Building HACS MCP server..."
    if docker-compose build hacs-mcp-server; then
        log_success "HACS MCP server built successfully"
    else
        log_error "Failed to build HACS MCP server"
        exit 1
    fi
    
    log_info "Starting HACS MCP server..."
    if docker-compose up -d hacs-mcp-server; then
        log_success "HACS MCP server started"
    else
        log_error "Failed to start HACS MCP server"
        exit 1
    fi
    
    # Wait for MCP server to be healthy
    if ! wait_for_service hacs-mcp-server 60; then
        log_error "HACS MCP server failed to start properly"
        docker-compose logs hacs-mcp-server
        exit 1
    fi
    
    # Step 4: Test MCP server connectivity
    log_section "🔧 Testing MCP Server"
    
    # Test MCP server endpoint
    if ! test_endpoint "http://localhost:8000" "HACS MCP Server" 30; then
        log_error "MCP server is not responding"
        docker-compose logs hacs-mcp-server
        exit 1
    fi
    
    # Test MCP tools list
    log_info "Testing MCP tools availability..."
    if response=$(curl -s --max-time 10 -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
        http://localhost:8000/); then
        
        # Extract tools count using basic string manipulation
        tools_count=$(echo "$response" | grep -o '"tools":\[' | wc -l)
        if [ "$tools_count" -gt 0 ]; then
            # Try to get actual count from the response
            actual_count=$(echo "$response" | grep -o '"name":"[^"]*"' | wc -l)
            log_success "MCP server has $actual_count healthcare tools available"
        else
            log_warning "MCP server responded but no tools found"
        fi
    else
        log_error "Failed to get tools list from MCP server"
        exit 1
    fi
    
    # Step 5: Test HACS agents
    log_section "🤖 Testing HACS Agents"
    
    # Change to the agent directory
    cd examples/hacs_developer_agent
    
    # Set up PYTHONPATH for the agents
    export PYTHONPATH="../../packages/hacs-models/src:../../packages/hacs-auth/src:../../packages/hacs-infrastructure/src:../../packages/hacs-core/src:../../packages/hacs-tools/src:../../packages/hacs-persistence/src:../../packages/hacs-registry/src:../../packages/hacs-utils/src:../../packages/hacs-cli/src:$PYTHONPATH"
    
    # Test DeepAgents-style HACS agent
    log_info "Testing DeepAgents-style HACS agent..."
    if uv run python deep_hacs_agent.py 2>/dev/null | grep -q "Healthcare Deep Agent created successfully"; then
        log_success "DeepAgents-style HACS agent is working"
    else
        log_warning "DeepAgents-style HACS agent test had issues (may be due to missing API keys)"
    fi
    
    # Return to root directory
    cd ../..
    
    # Step 6: Start LangGraph development server
    log_section "🚀 Starting LangGraph Development Server"
    
    cd examples/hacs_developer_agent
    
    log_info "Starting LangGraph dev server in background..."
    
    # Start LangGraph dev server in background
    nohup uv run langgraph dev --host 127.0.0.1 --port 2024 > langgraph.log 2>&1 &
    LANGGRAPH_PID=$!
    
    # Wait for LangGraph server to start
    log_info "Waiting for LangGraph server to start..."
    sleep 10
    
    # Test LangGraph server
    if test_endpoint "http://127.0.0.1:2024/docs" "LangGraph API" 15; then
        log_success "LangGraph development server is running"
        log_info "LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
        log_info "API Docs: http://127.0.0.1:2024/docs"
    else
        log_warning "LangGraph server may not be fully ready (this is sometimes normal)"
    fi
    
    cd ../..
    
    # Step 7: Final verification
    log_section "✅ Final System Verification"
    
    # Check all services are running
    services_status=()
    
    if docker-compose ps postgres | grep -q "healthy"; then
        services_status+=("✅ PostgreSQL: Healthy")
    else
        services_status+=("❌ PostgreSQL: Not healthy")
    fi
    
    if docker-compose ps hacs-mcp-server | grep -q "healthy"; then
        services_status+=("✅ HACS MCP Server: Healthy")
    else
        services_status+=("❌ HACS MCP Server: Not healthy")
    fi
    
    if curl -s --max-time 5 http://127.0.0.1:2024/docs >/dev/null 2>&1; then
        services_status+=("✅ LangGraph Server: Running")
    else
        services_status+=("⚠️ LangGraph Server: May not be ready")
    fi
    
    # Display service status
    for status in "${services_status[@]}"; do
        echo -e "  $status"
    done
    
    # Step 8: Setup completion and next steps
    log_section "🎉 Setup Complete!"
    
    echo -e "\n${GREEN}HACS LangGraph Agent Environment is Ready!${NC}\n"
    
    echo "📊 Service Status:"
    echo "  🐘 PostgreSQL Database: http://localhost:5432"
    echo "  🔧 HACS MCP Server: http://localhost:8000"
    echo "  🤖 LangGraph Dev Server: http://127.0.0.1:2024"
    echo "  🎨 LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
    
    echo ""
    echo "🏥 Available Agents:"
    echo "  • Original HACS Agent: hacs_agent"
    echo "  • DeepAgents HACS Agent: deep_hacs_agent"
    echo ""
    
    echo "🔧 Quick Commands:"
    echo "  • View logs: docker-compose logs [service_name]"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart services: docker-compose restart [service_name]"
    echo "  • Test MCP tools: curl -X POST -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}' http://localhost:8000/"
    echo ""
    
    echo "⚠️ Important Notes:"
    echo "  • Add your API keys to .env file for full agent functionality"
    echo "  • LangGraph Studio requires an account at smith.langchain.com"
    echo "  • Use 'docker-compose down' when you're done to clean up resources"
    echo ""
    
    echo "📚 Next Steps:"
    echo "  1. Open LangGraph Studio in your browser"
    echo "  2. Test the agents with healthcare scenarios"
    echo "  3. Explore the 25+ HACS healthcare tools"
    echo "  4. Build your own healthcare AI workflows"
    echo ""
    
    log_success "Setup completed successfully! 🚀"
}

# Cleanup function for graceful exit
cleanup() {
    log_info "Cleaning up..."
    # Kill LangGraph server if it was started
    if [ ! -z "$LANGGRAPH_PID" ]; then
        kill $LANGGRAPH_PID 2>/dev/null || true
    fi
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Run main function
main "$@"