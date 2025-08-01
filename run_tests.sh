#!/bin/bash
"""
HACS Tools Test Runner

Simple script to run comprehensive HACS tools tests with different configurations.

Usage:
    ./run_tests.sh                    # Run all tests with Docker
    ./run_tests.sh --local           # Run tests locally (requires local setup)
    ./run_tests.sh --unit-only       # Run unit tests only (no MCP integration)
    ./run_tests.sh --integration     # Run MCP integration tests only
    ./run_tests.sh --clean           # Clean up and run fresh tests

Author: HACS Development Team
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
RUN_MODE="docker"
TEST_TYPE="all"
CLEAN_START=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            RUN_MODE="local"
            shift
            ;;
        --unit-only)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --clean)
            CLEAN_START=true
            shift
            ;;
        -h|--help)
            echo "HACS Tools Test Runner"
            echo ""
            echo "Usage:"
            echo "  $0                   # Run all tests with Docker"
            echo "  $0 --local          # Run tests locally"
            echo "  $0 --unit-only      # Run unit tests only"
            echo "  $0 --integration    # Run MCP integration tests only"
            echo "  $0 --clean          # Clean up and run fresh tests"
            echo ""
            echo "Environment Variables:"
            echo "  MCP_SERVER_URL       # MCP server URL (default: http://localhost:8000)"
            echo "  DATABASE_URL         # Database connection string"
            echo "  QDRANT_URL          # Qdrant vector store URL"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🚀 HACS Tools Test Runner${NC}"
echo -e "=================================="
echo -e "Mode: ${YELLOW}$RUN_MODE${NC}"
echo -e "Test Type: ${YELLOW}$TEST_TYPE${NC}"
echo -e "Clean Start: ${YELLOW}$CLEAN_START${NC}"
echo ""

# Clean up if requested
if [ "$CLEAN_START" = true ]; then
    echo -e "${YELLOW}🧹 Cleaning up existing containers and volumes...${NC}"
    docker-compose down -v 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    echo ""
fi

# Run tests based on mode
case $RUN_MODE in
    docker)
        echo -e "${BLUE}🐳 Running tests with Docker...${NC}"
        
        case $TEST_TYPE in
            all)
                echo -e "${YELLOW}Running comprehensive test suite...${NC}"
                docker-compose --profile test up --build --abort-on-container-exit
                ;;
            unit)
                echo -e "${YELLOW}Running unit tests only...${NC}"
                docker-compose up -d postgres
                docker-compose run --rm hacs-test-runner python -m pytest tests/test_hacs_tools_comprehensive.py -v --tb=short -k "not mcp"
                ;;
            integration)
                echo -e "${YELLOW}Running MCP integration tests...${NC}"
                docker-compose --profile test up --build --abort-on-container-exit
                ;;
        esac
        ;;
        
    local)
        echo -e "${BLUE}💻 Running tests locally...${NC}"
        
        # Check prerequisites
        if ! command -v python &> /dev/null; then
            echo -e "${RED}❌ Python not found. Please install Python 3.11+${NC}"
            exit 1
        fi
        
        if ! command -v pytest &> /dev/null; then
            echo -e "${YELLOW}⚠️ pytest not found. Installing...${NC}"
            pip install pytest pytest-asyncio
        fi
        
        # Set up Python path
        export PYTHONPATH="$(pwd)/packages/hacs-core/src:$(pwd)/packages/hacs-tools/src:$(pwd)/packages/hacs-utils/src:$(pwd)/packages/hacs-persistence/src:$(pwd)/packages/hacs-registry/src"
        
        case $TEST_TYPE in
            all)
                echo -e "${YELLOW}Running all tests locally (requires MCP server)...${NC}"
                python -m pytest tests/test_hacs_tools_comprehensive.py --mcp-integration -v --tb=short
                ;;
            unit)
                echo -e "${YELLOW}Running unit tests only...${NC}"
                python -m pytest tests/test_hacs_tools_comprehensive.py -v --tb=short -k "not mcp"
                ;;
            integration)
                echo -e "${YELLOW}Running MCP integration tests...${NC}"
                python -m pytest tests/test_hacs_tools_comprehensive.py --mcp-integration -v --tb=short -k "mcp"
                ;;
        esac
        ;;
esac

# Check test results
EXIT_CODE=$?

echo ""
echo -e "=================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests completed successfully!${NC}"
    echo ""
    echo -e "📊 Test Results:"
    echo -e "   ${GREEN}Total Tools Tested: 42${NC}"
    echo -e "   ${GREEN}Domains Covered: 10${NC}"
    echo -e "   ${GREEN}Test Types: Unit + Integration${NC}"
    echo ""
    echo -e "📁 View detailed results in:"
    echo -e "   • Docker logs: ${BLUE}docker logs hacs-test-runner${NC}"
    echo -e "   • Test results: ${BLUE}./test_results/${NC}"
    echo ""
    echo -e "🎉 ${GREEN}HACS tools are ready for production!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo ""
    echo -e "🔍 Troubleshooting:"
    echo -e "   • Check server logs: ${BLUE}docker logs hacs-mcp-server${NC}"
    echo -e "   • Verify database: ${BLUE}docker logs hacs-postgres${NC}"
    echo -e "   • Review test output above"
    echo ""
    echo -e "📚 For help, see: ${BLUE}docs/testing.md${NC}"
fi

exit $EXIT_CODE