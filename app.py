from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-city-iam-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Database Models ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='User') # 'User' or 'Admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending') # 'Pending', 'Approved', 'Completed', 'Rejected'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to get user details easily
    user = db.relationship('User', backref=db.backref('requests', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'Admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role_select = request.form.get('role')
        admin_code = request.form.get('admin_code')

        # Basic Check
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))

        # Set Role
        role = 'User'
        if role_select == 'Admin':
            if admin_code == 'CITYADMIN2024': # Simple secret code for demo
                role = 'Admin'
            else:
                flash('Invalid Admin Secret Code.', 'danger')
                return redirect(url_for('signup'))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            if user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'User':
        return redirect(url_for('index'))
    
    # Get user requests
    requests = ServiceRequest.query.filter_by(user_id=current_user.id).order_by(ServiceRequest.timestamp.desc()).all()
    return render_template('user_dashboard.html', requests=requests)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'Admin':
        flash('Unauthorized Access!', 'danger')
        return redirect(url_for('index'))

    # Get all users and all requests
    users = User.query.all()
    all_requests = ServiceRequest.query.order_by(ServiceRequest.timestamp.desc()).all()
    return render_template('admin_dashboard.html', users=users, all_requests=all_requests)

# --- API Endpoints ---

@app.route('/request_service', methods=['POST'])
@login_required
def request_service():
    if current_user.role != 'User':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    service_name = data.get('service_name')
    
    if not service_name:
        return jsonify({'success': False, 'message': 'Service name required'}), 400
    
    new_request = ServiceRequest(user_id=current_user.id, service_name=service_name)
    db.session.add(new_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Request for {service_name} submitted successfully!'})

@app.route('/update_request_status', methods=['POST'])
@login_required
def update_request():
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    request_id = data.get('request_id')
    new_status = data.get('status')
    
    req = ServiceRequest.query.get(request_id)
    if not req:
        return jsonify({'success': False, 'message': 'Request not found'}), 404
    
    req.status = new_status
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Request status updated to {new_status}'})

@app.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    if current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot delete yourself!'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Delete associated requests first
    ServiceRequest.query.filter_by(user_id=user_id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'User {user.username} deleted successfully.'})

# Initialize Database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
