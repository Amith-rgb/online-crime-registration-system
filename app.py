from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, CrimeReport, Audit
from werkzeug.security import check_password_hash
from sqlalchemy import or_
import os
import io
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-me'
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}

db.init_app(app)
# Ensure DB tables/columns are created/migrated on startup (covers "flask run" and others)
from init_database import init_db
init_db(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# Routes
@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username taken.')
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registered! Log in now.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('splash'))

@app.route('/dashboard')
@login_required
def dashboard():
    reports = CrimeReport.query.filter_by(user_id=current_user.id).all()
    # include audits via relationship (available in template as report.audits)
    return render_template('status.html', reports=reports)

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report_crime():
    if request.method == 'POST':
        crime_type = request.form['crime_type']
        description = request.form['description']
        location = request.form.get('location', 'Unknown')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        image_path = None
        # handle attachment
        if 'attachment' in request.files:
            f = request.files['attachment']
            if f and f.filename and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(save_path)
                # store relative path
                image_path = os.path.join('instance', 'uploads', filename)
        report = CrimeReport(
            user_id=current_user.id,
            crime_type=crime_type,
            description=description,
            location=location,
            image_path=image_path,
            latitude=float(lat) if lat else None,
            longitude=float(lon) if lon else None
        )
        db.session.add(report)
        db.session.commit()
        flash('Report submitted!')
        return redirect(url_for('dashboard'))
    return render_template('report.html')

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Admin only!')
        return redirect(url_for('dashboard'))

    q = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    per_page = 15

    # build base filtered query (join User for username search)
    base = CrimeReport.query.outerjoin(User)
    if q:
        like = f'%{q}%'
        base = base.filter(or_(
            CrimeReport.description.ilike(like),
            CrimeReport.location.ilike(like),
            CrimeReport.crime_type.ilike(like),
            User.username.ilike(like)
        ))

    # --- compute totals from the filtered set (before pagination) ---
    total_reports = base.count()
    pending = base.filter(CrimeReport.status == 'Pending').count()
    investigating = base.filter(CrimeReport.status == 'Investigating').count()
    resolved = base.filter(CrimeReport.status == 'Resolved').count()
    # --- end totals ---

    pagination = base.order_by(CrimeReport.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    reports = pagination.items
    total_pages = pagination.pages or 1

    return render_template('admin.html',
                           reports=reports,
                           q=q,
                           page=page,
                           total_pages=total_pages,
                           total_reports=total_reports,
                           pending=pending,
                           investigating=investigating,
                           resolved=resolved)

@app.route('/admin/export')
@login_required
def export_reports():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    q = request.args.get('q', '').strip()
    query = CrimeReport.query.outerjoin(User)
    if q:
        like = f'%{q}%'
        query = query.filter(or_(
            CrimeReport.description.ilike(like),
            CrimeReport.location.ilike(like),
            CrimeReport.crime_type.ilike(like),
            User.username.ilike(like)
        ))

    reports = query.order_by(CrimeReport.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'user', 'crime_type', 'description', 'location', 'status', 'timestamp'])
    for r in reports:
        writer.writerow([
            r.id,
            (r.user.username if r.user else ''),
            r.crime_type,
            (r.description or '').replace('\n', ' '),
            r.location,
            r.status,
            r.timestamp.isoformat() if r.timestamp else ''
        ])

    resp = Response(output.getvalue(), mimetype='text/csv')
    resp.headers['Content-Disposition'] = 'attachment; filename=reports.csv'
    return resp

@app.route('/update_status/<int:report_id>', methods=['POST'])
@login_required
def update_status(report_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    status = request.json['status']
    report = CrimeReport.query.get(report_id)
    if report:
        old = report.status
        report.status = status
        # create audit
        audit = Audit(report_id=report.id, old_status=old, new_status=status, changed_by=current_user.id)
        db.session.add(audit)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Report not found'}), 404

if __name__ == '__main__':
    os.makedirs('instance', exist_ok=True)
    app.run(debug=True)