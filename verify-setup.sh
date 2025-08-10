#!/bin/bash

# HACS Setup Verification Script
# Verifies that all HACS components are working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local success_pattern="$3"
    
    echo -n "Testing $test_name... "
    
    if output=$(eval "$test_command" 2>&1); then
        if [[ -z "$success_pattern" ]] || echo "$output" | grep -q "$success_pattern"; then
            echo -e "${GREEN}✅ PASS${NC}"
            return 0
        else
            echo -e "${RED}❌ FAIL${NC} (pattern not found)"
            echo "Output: $output"
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (command failed)"
        echo "Output: $output"
        return 1
    fi
}

main() {
    log_section "🔍 HACS Setup Verification"
    
    local tests_passed=0
    local tests_total=0
    
    # Test 1: Docker services
    log_section "🐳 Docker Services"
    
    ((tests_total++))
    if run_test "PostgreSQL container" "docker-compose ps postgres" "healthy"; then
        ((tests_passed++))
    fi
    
    ((tests_total++))
    if run_test "HACS MCP Server container" "docker-compose ps hacs-mcp-server" "healthy"; then
        ((tests_passed++))
    fi
    
    # Test 2: Service endpoints
    log_section "🌐 Service Endpoints"
    
    ((tests_total++))
    if run_test "MCP Server HTTP endpoint" "curl -s --max-time 5 http://localhost:8000" ""; then
        ((tests_passed++))
    fi
    
    ((tests_total++))
    if run_test "LangGraph Server endpoint" "curl -s --max-time 5 http://127.0.0.1:2024/docs" ""; then
        ((tests_passed++))
    fi
    
    # Test 3: MCP Tools
    log_section "🔧 MCP Tools"
    
    ((tests_total++))
    if run_test "MCP tools list" "curl -s --max-time 10 -X POST -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}' http://localhost:8000/" "tools"; then
        ((tests_passed++))
    fi
    
    ((tests_total++))
    if run_test "MCP tool execution" "curl -s --max-time 15 -X POST -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"discover_hacs_resources\",\"arguments\":{\"category_filter\":\"clinical\",\"include_field_counts\":true}},\"id\":2}' http://localhost:8000/" "discover_hacs_resources completed"; then
        ((tests_passed++))
    fi
    
    # Test 4: HACS Agents
    log_section "🤖 HACS Agents"
    
    cd examples/hacs_developer_agent
    export PYTHONPATH="../../packages/hacs-models/src:../../packages/hacs-auth/src:../../packages/hacs-infrastructure/src:../../packages/hacs-core/src:../../packages/hacs-tools/src:../../packages/hacs-persistence/src:../../packages/hacs-registry/src:../../packages/hacs-utils/src:../../packages/hacs-cli/src:$PYTHONPATH"
    
    ((tests_total++))
    if run_test "DeepAgents HACS agent" "timeout 30 uv run python deep_hacs_agent.py" "Healthcare Deep Agent created successfully"; then
        ((tests_passed++))
    fi
    
    cd ../..
    
    # Test 5: LangGraph Integration
    log_section "🚀 LangGraph Integration"
    
    ((tests_total++))
    if run_test "LangGraph assistants API" "curl -s --max-time 10 http://127.0.0.1:2024/assistants" "graph_id"; then
        ((tests_passed++))
    fi
    
    # Summary
    log_section "📊 Verification Results"
    
    echo "Tests passed: $tests_passed/$tests_total"
    echo ""
    
    if [ $tests_passed -eq $tests_total ]; then
        log_success "All tests passed! HACS is fully operational 🎉"
        
        echo ""
        echo "🏥 Your HACS Environment is Ready:"
        echo "  • PostgreSQL Database: ✅ Running"
        echo "  • HACS MCP Server: ✅ Running (25+ Hacs Tools)"
        echo "  • LangGraph Server: ✅ Running"
        echo "  • Healthcare Agents: ✅ Functional"
        echo ""
        echo "🎯 Next Steps:"
        echo "  1. Open LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
        echo "  2. Test agents: hacs_agent and deep_hacs_agent"
        echo "  3. Try healthcare scenarios with the available tools"
        echo ""
        return 0
    else
        log_error "Some tests failed. HACS may not be fully functional."
        echo ""
        echo "🔧 Troubleshooting:"
        echo "  • Check service logs: docker-compose logs [service]"
        echo "  • Restart services: docker-compose restart"
        echo "  • Re-run setup: ./setup.sh"
        echo ""
        return 1
    fi
}

main "$@"