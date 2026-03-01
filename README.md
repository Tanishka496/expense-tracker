# Expense Tracker 💰

A modern, elegant expense tracking web application built with Flask and SQLite.

## Features

✨ **Add Expenses** - Record expenses with amount, category, description, and date
📊 **Track Spending** - View total expenses and monthly breakdowns
💾 **Persistent Storage** - All data saved to SQLite database
🎨 **Modern UI** - Beautiful, responsive design with smooth animations
📱 **Mobile Friendly** - Works seamlessly on desktop and mobile devices

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, Jinja2 Templates
- **Fonts**: Google Fonts (Inter, Poppins)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/expense-tracker.git
cd expense-tracker
```

2. Create and activate virtual environment:
```bash
python -m venv venv
./venv/Scripts/activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and visit: `http://127.0.0.1:5000`

## Project Structure

```
expense-tracker/
├── app.py                 # Main Flask application
├── expenses.db            # SQLite database
├── requirements.txt       # Project dependencies
├── .gitignore            # Git ignore rules
└── templates/
    └── index.html        # Main HTML template
```

## Features in Detail

### Add Expense
- Fill in the amount, category, description, and date
- Click "Add Expense" to save
- Data is automatically persisted to database

### View Summary
- Total expense amount displayed prominently
- Monthly breakdown showing expenses per month
- Complete expense history in table format

### Categories
- Food 🍔
- Transportation 🚗
- Entertainment 🎬
- Utilities 💡
- Healthcare 🏥
- Shopping 🛍️
- Other 📌

## Deployment

This app is ready to deploy on:
- Azure App Service
- Heroku
- AWS
- DigitalOcean
- Any platform that supports Python/WSGI

## Future Enhancements

- Delete/Edit expenses
- Budget limits and alerts
- Expense reports and analytics
- Multi-user support with authentication
- Export to CSV/PDF
- Dark mode

## License

MIT License

## Author

Created with ❤️
