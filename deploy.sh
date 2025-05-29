#!/bin/bash

# Deployment script for Alabaranes UNEI Flask Application (Development Environment)
# This script sets up the application to run as a systemd service on Ubuntu

set -e

# Configuration
APP_NAME="alabaranes-unei"
APP_DIR="/opt/$APP_NAME"
SERVICE_FILE="$APP_NAME.service"
PYTHON_VERSION="python3"

echo "Starting deployment of $APP_NAME (Development Environment)..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (use sudo)"
    exit 1
fi

# Update system packages
echo "Updating system packages..."
apt update

# Install required system packages
echo "Installing required packages..."
apt install -y python3 python3-pip python3-venv

# Create application directory
echo "Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

# Copy application files (assuming script is run from source directory)
echo "Copying application files..."
cp -r /path/to/your/source/* $APP_DIR/
# Note: Replace /path/to/your/source with the actual path to your application

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_VERSION -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create database directory if it doesn't exist
mkdir -p $APP_DIR/database

# Set proper ownership and permissions
echo "Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod 644 $APP_DIR/database/database.db 2>/dev/null || true

# Copy systemd service file
echo "Installing systemd service..."
cp $SERVICE_FILE /etc/systemd/system/

# Reload systemd and enable service
echo "Configuring systemd service..."
systemctl daemon-reload
systemctl enable $SERVICE_FILE
systemctl start $SERVICE_FILE

# Check service status
echo "Checking service status..."
systemctl status $SERVICE_FILE --no-pager

echo ""
echo "Development deployment completed!"
echo "Service status: $(systemctl is-active $SERVICE_FILE)"
echo "Application should be running on http://localhost:5000"
echo ""
echo "Development Environment Settings:"
echo "  - DEBUG_MODE: True"
echo "  - FLASK_ENV: development"
echo "  - Secret Key: Using development key (change for production!)"
echo ""
echo "Useful commands:"
echo "  Check status: sudo systemctl status $SERVICE_FILE"
echo "  Start service: sudo systemctl start $SERVICE_FILE"
echo "  Stop service: sudo systemctl stop $SERVICE_FILE"
echo "  Restart service: sudo systemctl restart $SERVICE_FILE"
echo "  View logs: sudo journalctl -u $SERVICE_FILE -f"
echo ""
echo "Note: Update the source path in this script before running!"
echo "Warning: This is configured for DEVELOPMENT only - not suitable for production!" 