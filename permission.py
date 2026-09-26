from datetime import datetime, timezone
from models import db

class DocumentPermission(db.Model):
    __tablename__ = 'document_permissions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    role = db.Column(db.String(30), nullable=True) # E.g., 'HR', 'EMPLOYEE', or NULL for all
    department = db.Column(db.String(60), nullable=True) # E.g., 'Engineering', or NULL for all
    access_level = db.Column(db.String(20), nullable=False, default='READ') # READ, DENIED
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'role': self.role,
            'department': self.department,
            'access_level': self.access_level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
