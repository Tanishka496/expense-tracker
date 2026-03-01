# Deployment Guide for Azure

## Step 1: Push to GitHub

### A. Create Repository on GitHub
1. Go to https://github.com/new
2. Repository name: `expense-tracker`
3. Description: "Elegant expense tracking web application"
4. Choose Public or Private
5. Click "Create repository"

### B. Push Code from Your Machine
```bash
cd "c:\Users\TANISHKA\OneDrive\Desktop\IOT PROJECT"

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/expense-tracker.git

# Rename branch to main (Azure requires this)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 2: Deploy on Azure

### A. Create Web App
1. Go to https://portal.azure.com
2. Click "Create a resource"
3. Search for "Web App" → Click Create
4. Fill in details:
   - **Subscription**: Your subscription
   - **Resource Group**: Create new (expense-tracker-rg)
   - **Name**: `expense-tracker-[YOUR_NAME]` (must be unique)
   - **Runtime stack**: Python 3.13
   - **Operating System**: Linux
   - **App Service Plan**: Create F1 (Free) plan
5. Click "Review + Create" → "Create"

### B. Configure Deployment
1. Go to newly created Web App
2. Left menu → "Deployment Center"
3. Click "Settings" tab
4. Source: GitHub (Authorize GitHub)
5. Organization: Your GitHub username
6. Repository: expense-tracker
7. Branch: main
8. Click Save

### C. Configure Python Environment
1. In Web App → "Configuration"
2. Add Application settings:
   - Name: `SCM_DO_BUILD_DURING_DEPLOYMENT`
   - Value: `true`
3. Click "Save"

### D. Monitor Deployment
1. Go to "Deployment slots" → Activity logs
2. Wait for successful deployment (green checkmark)
3. Your app will be available at:
   `https://[your-app-name].azurewebsites.net`

### E. Test Live URL
- Open your deployed URL in browser
- Test adding an expense
- Verify database functionality

## Project Files Ready:
✅ requirements.txt - All Python dependencies
✅ Procfile - Web server configuration
✅ runtime.txt - Python version specification
✅ .gitignore - Files to exclude from Git
✅ README.md - Project documentation
✅ app.py - Flask application
✅ templates/index.html - Web interface

## Troubleshooting

If deployment fails:
1. Check Build logs in Azure App Service
2. Verify requirements.txt has all dependencies
3. Check if port 80 is being used (not port 5000)
4. Ensure SQLite database permissions are correct

## Next Steps (After Deployment)
- Domain name configuration
- Custom SSL certificate
- Database backups
- Monitoring and logging setup
