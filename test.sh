#!/bin/bash
# Linux/Mac script to run tests inside Docker container

show_usage() {
    echo "========================================"
    echo "Running Auto-Apply Tests in Docker"
    echo "========================================"
    echo ""
    echo "Usage:"
    echo "  ./test.sh stats              - Show statistics"
    echo "  ./test.sh browser            - Test browser service"
    echo "  ./test.sh apply USER_ID      - Test auto-apply"
    echo "  ./test.sh monitor APP_ID     - Test monitoring"
    echo ""
    echo "Examples:"
    echo "  ./test.sh stats"
    echo "  ./test.sh browser"
    echo "  ./test.sh apply 507f1f77bcf86cd799439011"
    echo "  ./test.sh monitor 507f1f77bcf86cd799439012"
}

if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

case "$1" in
    stats)
        docker exec -it visionai-backend-1 python scripts/test_auto_apply.py --stats
        ;;
    browser)
        docker exec -it visionai-backend-1 python scripts/test_auto_apply.py --test-browser
        ;;
    apply)
        if [ -z "$2" ]; then
            echo "Error: User ID required"
            echo "Usage: ./test.sh apply USER_ID"
            exit 1
        fi
        docker exec -it visionai-backend-1 python scripts/test_auto_apply.py --user-id "$2"
        ;;
    monitor)
        if [ -z "$2" ]; then
            echo "Error: Application ID required"
            echo "Usage: ./test.sh monitor APP_ID"
            exit 1
        fi
        docker exec -it visionai-backend-1 python scripts/test_auto_apply.py --test-monitoring --app-id "$2"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run './test.sh' without arguments to see usage"
        exit 1
        ;;
esac
