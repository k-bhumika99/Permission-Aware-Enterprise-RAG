from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    department = db.Column(db.String(60), nullable=False, default='Engineering')
    role = db.Column(db.String(30), nullable=False, default='EMPLOYEE') # ADMIN, MANAGER, HR, EMPLOYEE
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    documents = db.relationship('Document', backref='owner', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

    def __init__(self, name=None, email=None, password_hash=None, department=None, role=None, is_active=True, **kwargs):
        super().__init__()
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if password_hash is not None:
            self.password_hash = password_hash
        if department is not None:
            self.department = department
        if role is not None:
            self.role = role
        if is_active is not None:
            self.is_active = is_active
        for k, v in kwargs.items():
            setattr(self, k, v)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
