# Development Deployment Guide for Alabaranes UNEI

This guide explains how to deploy the Alabaranes UNEI Flask application as a systemd service on Ubuntu in a **development environment**.

⚠️ **Warning**: This configuration is for development/testing only and should not be used in production!

## Prerequisites

- Ubuntu 18.04 or later
- Root or sudo access
- Python 3.6 or later

## Quick Deployment

1. **Copy your application files to the server**
2. **Edit the deployment script** (`deploy.sh`) and update the source path
3. **Run the deployment script**:
   ```bash
   sudo chmod +x deploy.sh
   sudo ./deploy.sh
   ```

## Manual Deployment Steps

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### 2. Create Application Directory

```bash
sudo mkdir -p /opt/alabaranes-unei
sudo cp -r /path/to/your/source/* /opt/alabaranes-unei/
cd /opt/alabaranes-unei
```

### 3. Set Up Python Virtual Environment

```bash
sudo python3 -m venv venv
sudo /opt/alabaranes-unei/venv/bin/pip install --upgrade pip
sudo /opt/alabaranes-unei/venv/bin/pip install -r requirements.txt
```

### 4. Create Database Directory

```bash
sudo mkdir -p /opt/alabaranes-unei/database
```

### 5. Set Proper Permissions

```bash
sudo chown -R www-data:www-data /opt/alabaranes-unei
sudo chmod -R 755 /opt/alabaranes-unei
```

### 6. Install Systemd Service

```bash
sudo cp alabaranes-unei.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable alabaranes-unei.service
sudo systemctl start alabaranes-unei.service
```

## Service Management

### Check Service Status
```bash
sudo systemctl status alabaranes-unei
```

### Start/Stop/Restart Service
```bash
sudo systemctl start alabaranes-unei
sudo systemctl stop alabaranes-unei
sudo systemctl restart alabaranes-unei
```

### View Logs
```bash
sudo journalctl -u alabaranes-unei -f
```

## Development Configuration

### Environment Variables

The systemd service file is configured with these development settings:

- `SECRET_KEY`: Simple development key (not secure for production!)
- `DATABASE_URL`: SQLite database in local directory
- `DEBUG_MODE`: Set to `True` for development features
- `FLASK_ENV`: Set to `development` for Flask development mode

### Service Configuration

Key configuration in the systemd service file:

- **User/Group**: Runs as `www-data` for consistency
- **Working Directory**: `/opt/alabaranes-unei`
- **Auto-restart**: Service automatically restarts on failure (5-second delay)
- **Logging**: Outputs to syslog with identifier `alabaranes-unui-dev`
- **Debug Mode**: Enabled for development

## Development Features

With `DEBUG_MODE=True` and `FLASK_ENV=development`, you get:

1. **Detailed error pages** with stack traces
2. **Auto-reload** when code changes (may require restart)
3. **Flask development server features**
4. **Bypassed stock verification** (as per your app's debug mode)

## Security Note

⚠️ **This configuration is NOT secure for production use**:

1. **Weak Secret Key**: Uses a simple, known development key
2. **Debug Mode Enabled**: Exposes sensitive information in errors
3. **Development Environment**: Flask runs in development mode
4. **No HTTPS**: No SSL/TLS encryption configured

## Converting to Production

When ready for production deployment:

1. **Change environment variables**:
   - Generate secure `SECRET_KEY`
   - Set `DEBUG_MODE=False`
   - Set `FLASK_ENV=production`

2. **Add reverse proxy** (Nginx/Apache)
3. **Configure SSL/TLS**
4. **Use production database** (PostgreSQL/MySQL)
5. **Implement proper logging**

## Troubleshooting

### Service Won't Start

1. Check service status: `sudo systemctl status alabaranes-unei`
2. View logs: `sudo journalctl -u alabaranes-unei -n 50`
3. Verify file permissions: `ls -la /opt/alabaranes-unei`
4. Test Python environment: `sudo -u www-data /opt/alabaranes-unei/venv/bin/python -c "import flask"`

### Common Issues

1. **Permission denied**: Check file ownership and permissions
2. **Module not found**: Ensure virtual environment is properly set up
3. **Database errors**: Verify database directory exists and is writable
4. **Port conflicts**: Ensure port 5000 is not in use by another service

### Development Debugging

Since this is a development environment:

- **Flask debugger** is enabled - detailed error pages will show
- **Live code changes** - restart service to pick up changes
- **Debug logs** - more verbose logging available

### Logs Location

- Service logs: `sudo journalctl -u alabaranes-unei`
- System logs: `/var/log/syslog` (filtered by `alabaranes-unei-dev`)

## Backup

Important files to backup:
- Database: `/opt/alabaranes-unei/database/database.db`
- Configuration: `/etc/systemd/system/alabaranes-unei.service`
- Application files: `/opt/alabaranes-unei/`

## Updates

To update the application:

1. Stop the service: `sudo systemctl stop alabaranes-unei`
2. Backup the database
3. Update application files
4. Install new dependencies if needed
5. Start the service: `sudo systemctl start alabaranes-unei`

## Development Workflow

For active development:

```bash
# Stop the service
sudo systemctl stop alabaranes-unei

# Make your changes to the code
# ...

# Restart the service
sudo systemctl start alabaranes-unei

# Monitor logs for issues
sudo journalctl -u alabaranes-unei -f
``` 