# Online Crime Registration System

A streamlined web-based platform designed to register, track, and manage crime reports online.  
This project was developed as part of an academic submission, with a strong focus on backend workflow, secure data handling, and clean UI/UX flow.

---

## 🚀 Features

### 👤 User Module
- User registration & login  
- Submit crime reports  
- Track report status  
- View submitted complaints  

### 👨‍💼 Admin Module
- Admin authentication  
- View all registered complaints  
- Update complaint status  
- Manage user records  

---

## 🛠️ Tech Stack

**Backend:** Python (Flask)  
**Frontend:** HTML, CSS, JavaScript  
**Database:** SQLite  
**Templates:** Jinja2  
**Version Control:** Git & GitHub  

---

## 📂 Project Structure

```bash
project/
│
├── app.py                 # Main Flask application
├── models.py              # Database models and ORM setup
├── init_database.py       # Initial database setup script
│
├── templates/             # HTML templates (User/Admin pages)
├── static/                # CSS & JS assets
│
├── instance/              # Local SQLite DB (ignored from Git)
└── __pycache__/           # Python cache files (ignored)
```

⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/Amith-rgb/online-crime-registration-system.git
cd online-crime-registration-system

2️⃣ Install dependencies
pip install flask

3️⃣ Initialize the database
python init_database.py

4️⃣ Run the application
python app.py


The system will be available at:

http://127.0.0.1:5000/
🤝 Contribution

Pull requests are welcome.
For major changes, please open an issue first to discuss your ideas.

📄 License

This project is open-source and available under the MIT License.

🙋‍♂️ Author

Amith
GitHub: https://github.com/Amith-rgb
