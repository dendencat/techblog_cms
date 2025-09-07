#!/bin/bash

# TechBlog CMS Control Script
# Usage: ./cms-ctl.sh <init|db|container> [options...]

set -e

# Function to display help
show_help() {
    echo "Usage: $0 <command> [options...]"
    echo ""
    echo "Commands:"
    echo "  init           Initialize or setup the CMS"
    echo "  db             Database operations"
    echo "  container      Container management"
    echo ""
    echo "Database operations:"
    echo "  $0 db --backup [--path /path/to/backup/dir]"
    echo "  $0 db --restore --file /path/to/backup.sql"
    echo ""
    echo "Options:"
    echo "  --backup          Create database backup"
    echo "  --restore         Restore database from backup"
    echo "  --path DIR        Backup directory (default: current directory)"
    echo "  --file FILE       Backup file path for restore"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 db --backup"
    echo "  $0 db --backup --path ./backups"
    echo "  $0 db --restore --file ./backup/backup_20250907.sql"
}

# Function to display init help
show_init_help() {
    echo "Usage: $0 init [options...]"
    echo ""
    echo "Initialize or setup the TechBlog CMS."
    echo ""
    echo "This command will perform initial setup operations such as:"
    echo "  - Database initialization"
    echo "  - Static files collection"
    echo "  - Initial data creation"
    echo ""
    echo "Options:"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 init"
}

# Function to display db help
show_db_help() {
    echo "Usage: $0 db <command> [options...]"
    echo ""
    echo "Database operations for TechBlog CMS."
    echo ""
    echo "Commands:"
    echo "  --backup          Create database backup"
    echo "  --restore         Restore database from backup"
    echo ""
    echo "Options:"
    echo "  --path DIR        Backup directory (default: current directory)"
    echo "  --file FILE       Backup file path for restore"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 db --backup"
    echo "  $0 db --backup --path ./backups"
    echo "  $0 db --restore --file ./backup/backup_20250907.sql"
}

# Function to display container help
show_container_help() {
    echo "Usage: $0 container <command> [options...]"
    echo ""
    echo "Container management operations for TechBlog CMS."
    echo ""
    echo "Commands:"
    echo "  --start           Start all containers"
    echo "  --stop            Stop all containers"
    echo "  --restart         Restart all containers"
    echo "  --status          Show container status"
    echo "  --logs            Show container logs"
    echo ""
    echo "Options:"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 container --start"
    echo "  $0 container --status"
    echo "  $0 container --logs django"
}

# Check if no arguments provided
if [[ $# -eq 0 ]]; then
    show_help
    exit 0
fi

# Get the command
COMMAND="$1"
shift

# Check if help is requested for a specific command
if [[ $# -eq 1 && "$1" == "--help" ]]; then
    case $COMMAND in
        init)
            show_init_help
            exit 0
            ;;
        db)
            show_db_help
            exit 0
            ;;
        container)
            show_container_help
            exit 0
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown command: $COMMAND"
            echo "Available commands: init, db, container"
            echo "Use '$0 --help' for usage information"
            exit 1
            ;;
    esac
fi

# Default values
BACKUP_DIR="$(pwd)"
BACKUP_FILE=""
ACTION=""

# Parse subcommand arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup)
            ACTION="backup"
            shift
            ;;
        --restore)
            ACTION="restore"
            shift
            ;;
        --path)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Handle commands
case $COMMAND in
    init)
        echo "Initializing TechBlog CMS..."
        # Add initialization logic here
        echo "✅ Initialization completed"
        ;;
        
    db)
        # Validate arguments for db command
        if [[ -z "$ACTION" ]]; then
            echo "Error: Must specify --backup or --restore for db command"
            echo "Use '$0 db --help' for usage information"
            exit 1
        fi

        if [[ "$ACTION" == "restore" && -z "$BACKUP_FILE" ]]; then
            echo "Error: --file is required for restore"
            echo "Use '$0 db --help' for usage information"
            exit 1
        fi

        # Check if Docker Compose is running
        if ! docker-compose ps | grep -q "Up"; then
            echo "Error: Docker Compose services are not running"
            echo "Please run 'docker-compose up -d' first"
            exit 1
        fi

        case $ACTION in
            backup)
                echo "Creating database backup..."
                
                # Create backup directory if it doesn't exist
                mkdir -p "$BACKUP_DIR"
                
                # Generate backup filename
                BACKUP_FILENAME="backup_$(date +%Y%m%d_%H%M%S).sql"
                BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILENAME"
                
                echo "Backup will be saved to: $BACKUP_PATH"
                
                # Execute backup
                if docker-compose exec -T db pg_dump -U techblog -h localhost techblogdb > "$BACKUP_PATH"; then
                    echo -e "\033[0;32m✅ Backup completed successfully: $BACKUP_PATH\033[0m"
                    echo "File size: $(du -h "$BACKUP_PATH" | cut -f1)"
                else
                    echo -e "\033[0;31m❌ Backup failed\033[0m"
                    exit 1
                fi
                ;;
                
            restore)
                if [[ ! -f "$BACKUP_FILE" ]]; then
                    echo "Error: Backup file not found: $BACKUP_FILE"
                    exit 1
                fi
                
                echo "Restoring database from: $BACKUP_FILE"
                echo "⚠️  This will overwrite existing data. Continue? (y/N)"
                read -r confirm
                if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
                    echo "Restore cancelled"
                    exit 0
                fi
                
                # Execute restore
                if docker-compose exec -T db psql -U techblog -h localhost techblogdb < "$BACKUP_FILE"; then
                    echo -e "\033[0;32m✅ Restore completed successfully\033[0m"
                    
                    # Run Django migrations after restore
                    echo "Running Django migrations..."
                    docker-compose exec django python manage.py migrate --noinput
                    
                    echo -e "\033[0;32m✅ Database migration completed\033[0m"
                else
                    echo -e "\033[0;31m❌ Restore failed\033[0m"
                    exit 1
                fi
                ;;
        esac
        ;;
        
    container)
        echo "Container management operations..."
        # Add container management logic here
        echo "Available containers:"
        docker-compose ps
        ;;
        
    --help)
        show_help
        exit 0
        ;;
        
    *)
        echo "Unknown command: $COMMAND"
        echo "Available commands: init, db, container"
        echo "Use '$0 --help' for usage information"
        exit 1
        ;;
esac

# Only show completion message for actual operations, not for help
if [[ "$COMMAND" != "--help" && "$1" != "--help" ]]; then
    echo "Operation completed."
fi
