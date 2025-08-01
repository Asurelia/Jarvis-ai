#!/bin/bash
# JARVIS Database Management Script for Linux/Mac
# Comprehensive database administration tool

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logo and header
print_header() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "    JARVIS AI Database Management"
    echo "=========================================="
    echo -e "${NC}"
}

# Print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python and required modules are available
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi

    if ! python3 -c "import asyncio" &> /dev/null; then
        print_error "Python asyncio module not available"
        exit 1
    fi
}

# Initialize database
init_database() {
    print_header
    print_info "Initializing JARVIS Database..."
    echo

    if python3 database/scripts/init_database.py; then
        print_success "Database initialization completed successfully!"
    else
        print_error "Database initialization failed!"
        exit 1
    fi
}

# Create backup
create_backup() {
    print_header
    print_info "Creating Database Backup..."
    echo

    echo "Choose backup type:"
    echo "1. Full backup (all services)"
    echo "2. PostgreSQL only"
    echo "3. Redis only"
    echo "4. ChromaDB only"
    echo

    read -p "Enter choice (1-4): " backup_choice

    case $backup_choice in
        1)
            python3 -m database.cli.jarvis_db_cli backup create --service all --type full
            ;;
        2)
            python3 -m database.cli.jarvis_db_cli backup create --service postgresql --type full
            ;;
        3)
            python3 -m database.cli.jarvis_db_cli backup create --service redis --type full
            ;;
        4)
            python3 -m database.cli.jarvis_db_cli backup create --service chromadb --type full
            ;;
        *)
            print_error "Invalid choice"
            return 1
            ;;
    esac

    print_success "Backup operation completed!"
}

# Restore from backup
restore_backup() {
    print_header
    print_warning "Database Restore Operation"
    echo

    print_warning "This will overwrite existing data!"
    read -p "Are you sure you want to continue? (y/N): " confirm

    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_info "Restore operation cancelled"
        return 0
    fi

    echo
    echo "Choose service to restore:"
    echo "1. PostgreSQL"
    echo "2. Redis"
    echo "3. ChromaDB"
    echo

    read -p "Enter choice (1-3): " restore_choice
    read -p "Enter full path to backup file: " backup_path

    if [[ ! -f "$backup_path" ]]; then
        print_error "Backup file not found: $backup_path"
        return 1
    fi

    case $restore_choice in
        1)
            python3 -m database.cli.jarvis_db_cli backup restore --service postgresql "$backup_path"
            ;;
        2)
            python3 -m database.cli.jarvis_db_cli backup restore --service redis "$backup_path"
            ;;
        3)
            python3 -m database.cli.jarvis_db_cli backup restore --service chromadb "$backup_path"
            ;;
        *)
            print_error "Invalid choice"
            return 1
            ;;
    esac

    print_success "Restore operation completed!"
}

# Health check
health_check() {
    print_header
    print_info "Running Database Health Check..."
    echo

    python3 -m database.cli.jarvis_db_cli health check
}

# Schedule management
manage_schedule() {
    print_header
    print_info "Backup Schedule Management"
    echo

    echo "Choose operation:"
    echo "1. View schedule status"
    echo "2. Start scheduler"
    echo "3. Manual backup"
    echo

    read -p "Enter choice (1-3): " sched_choice

    case $sched_choice in
        1)
            python3 -m database.cli.jarvis_db_cli schedule status
            ;;
        2)
            print_info "Starting backup scheduler..."
            print_warning "Press Ctrl+C to stop"
            python3 -m database.cli.jarvis_db_cli schedule start
            ;;
        3)
            python3 -m database.cli.jarvis_db_cli backup create --service all --type full
            ;;
        *)
            print_error "Invalid choice"
            return 1
            ;;
    esac
}

# Retention management
manage_retention() {
    print_header
    print_info "Data Retention Management"
    echo

    echo "Choose operation:"
    echo "1. View retention statistics"
    echo "2. Preview cleanup (dry run)"
    echo "3. Execute cleanup"
    echo

    read -p "Enter choice (1-3): " ret_choice

    case $ret_choice in
        1)
            python3 -m database.cli.jarvis_db_cli retention stats
            ;;
        2)
            python3 -m database.cli.jarvis_db_cli retention cleanup --dry-run
            ;;
        3)
            print_warning "This will permanently delete old data!"
            read -p "Continue? (y/N): " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                python3 -m database.cli.jarvis_db_cli retention cleanup
            else
                print_info "Cleanup cancelled"
            fi
            ;;
        *)
            print_error "Invalid choice"
            return 1
            ;;
    esac
}

# Service management
manage_service() {
    print_header
    print_info "Database Backup Service"
    echo

    echo "Choose operation:"
    echo "1. Start service (daemon mode)"
    echo "2. Check service status"
    echo "3. Test backup"
    echo "4. Health check"
    echo "5. Stop service (if running)"
    echo

    read -p "Enter choice (1-5): " serv_choice

    case $serv_choice in
        1)
            print_info "Starting backup service..."
            print_warning "Press Ctrl+C to stop"
            python3 database/scripts/backup_service.py
            ;;
        2)
            python3 database/scripts/backup_service.py --status
            ;;
        3)
            python3 database/scripts/backup_service.py --test-backup
            ;;
        4)
            python3 database/scripts/backup_service.py --health-check
            ;;
        5)
            print_info "Stopping service..."
            pkill -f "backup_service.py" || print_warning "No running service found"
            ;;
        *)
            print_error "Invalid choice"
            return 1
            ;;
    esac
}

# Launch CLI
launch_cli() {
    print_header
    print_info "Launching Database CLI Interface..."
    echo
    print_info "Type 'exit' or Ctrl+C to return to main menu"
    echo

    python3 -m database.cli.jarvis_db_cli
}

# View logs
view_logs() {
    print_header
    print_info "Database Logs"
    echo

    if [[ -f "logs/backup_service.log" ]]; then
        echo "Recent backup service logs:"
        echo "----------------------------------------"
        tail -n 20 logs/backup_service.log
        echo
    else
        print_warning "No backup service logs found"
    fi

    if [[ -f "logs/jarvis.log" ]]; then
        echo "Recent application logs:"
        echo "----------------------------------------"
        tail -n 10 logs/jarvis.log
        echo
    else
        print_warning "No application logs found"
    fi
}

# Docker operations
docker_operations() {
    print_header
    print_info "Docker Database Services"
    echo

    echo "Choose operation:"
    echo "1. Start database services"
    echo "2. Stop database services"
    echo "3. View service status"
    echo "4. View service logs"
    echo "5. Restart services"
    echo

    read -p "Enter choice (1-5): " docker_choice

    case $docker_choice in
        1)
            print_info "Starting database services..."
            docker-compose -f docker-compose.database.yml up -d
            ;;
        2)
            print_info "Stopping database services..."
            docker-compose -f docker-compose.database.yml down
            ;;
        3)
            docker-compose -f docker-compose.database.yml ps
            ;;
        4)
            echo "Choose service to view logs:"
            echo "1. Backup Service"
            echo "2. Health Monitor"
            echo "3. Retention Service"
            echo "4. Admin Interface"
            read -p "Enter choice (1-4): " log_choice
            
            case $log_choice in
                1) docker-compose -f docker-compose.database.yml logs backup-service ;;
                2) docker-compose -f docker-compose.database.yml logs db-health-monitor ;;
                3) docker-compose -f docker-compose.database.yml logs retention-service ;;
                4) docker-compose -f docker-compose.database.yml logs db-admin ;;
                *) print_error "Invalid choice" ;;
            esac
            ;;
        5)
            print_info "Restarting database services..."
            docker-compose -f docker-compose.database.yml restart
            ;;
        *)
            print_error "Invalid choice"
            return 1
            ;;
    esac
}

# Show help
show_help() {
    print_header
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  init         Initialize database with schema and data"
    echo "  backup       Create database backups"
    echo "  restore      Restore from backup files"
    echo "  health       Run health checks on all services"
    echo "  schedule     Manage backup scheduling"
    echo "  retention    Manage data retention policies"
    echo "  service      Control backup service daemon"
    echo "  cli          Launch interactive CLI"
    echo "  logs         View recent logs"
    echo "  docker       Manage Docker database services"
    echo "  help         Show this help message"
    echo
    echo "Interactive Mode:"
    echo "  Run without arguments to enter interactive menu"
    echo
    echo "Examples:"
    echo "  $0 init                    # Initialize database"
    echo "  $0 backup                  # Interactive backup"
    echo "  $0 health                  # Check system health"
    echo "  $0 service                 # Start backup service"
    echo
    echo "For detailed CLI options:"
    echo "  python3 -m database.cli.jarvis_db_cli --help"
    echo
}

# Interactive menu
interactive_menu() {
    while true; do
        print_header
        echo "Choose an operation:"
        echo
        echo "1.  Initialize Database"
        echo "2.  Create Backup"
        echo "3.  Restore Backup"
        echo "4.  Health Check"
        echo "5.  Schedule Management"
        echo "6.  Retention Management"
        echo "7.  Service Management"
        echo "8.  CLI Interface"
        echo "9.  View Logs"
        echo "10. Docker Operations"
        echo "11. Help"
        echo "12. Exit"
        echo

        read -p "Enter your choice (1-12): " choice

        case $choice in
            1) init_database; read -p "Press Enter to continue..." ;;
            2) create_backup; read -p "Press Enter to continue..." ;;
            3) restore_backup; read -p "Press Enter to continue..." ;;
            4) health_check; read -p "Press Enter to continue..." ;;
            5) manage_schedule; read -p "Press Enter to continue..." ;;
            6) manage_retention; read -p "Press Enter to continue..." ;;
            7) manage_service; read -p "Press Enter to continue..." ;;
            8) launch_cli ;;
            9) view_logs; read -p "Press Enter to continue..." ;;
            10) docker_operations; read -p "Press Enter to continue..." ;;
            11) show_help; read -p "Press Enter to continue..." ;;
            12) print_success "Goodbye! JARVIS Database Management exiting..."; exit 0 ;;
            *) print_error "Invalid choice. Please try again."; sleep 2 ;;
        esac
    done
}

# Main script logic
main() {
    # Check dependencies
    check_dependencies

    # Handle command line arguments
    case "${1:-}" in
        init) init_database ;;
        backup) create_backup ;;
        restore) restore_backup ;;
        health) health_check ;;
        schedule) manage_schedule ;;
        retention) manage_retention ;;
        service) manage_service ;;
        cli) launch_cli ;;
        logs) view_logs ;;
        docker) docker_operations ;;
        help) show_help ;;
        "") interactive_menu ;;
        *) print_error "Unknown command: $1"; show_help; exit 1 ;;
    esac
}

# Run main function
main "$@"