import json
from datetime import datetime, timezone
from models import db

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(20), nullable=False, default='txt')
    department = db.Column(db.String(60), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    classification = db.Column(db.String(30), nullable=False, default='INTERNAL') # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    allowed_roles_json = db.Column(db.Text, nullable=False, default='["ADMIN","HR","MANAGER","EMPLOYEE"]')
    allowed_departments_json = db.Column(db.Text, nullable=False, default='["ALL"]')
    sensitivity = db.Column(db.String(30), nullable=False, default='MEDIUM') # LOW, MEDIUM, HIGH, TOP_SECRET
    chunk_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    chunks = db.relationship('DocumentChunk', backref='document', cascade='all, delete-orphan', lazy=True)

    def __init__(self, title=None, filename=None, file_path=None, file_type='txt', department=None, owner_id=None, owner=None, classification='INTERNAL', allowed_roles=None, allowed_departments=None, sensitivity='MEDIUM', chunk_count=0, **kwargs):
        super().__init__()
        if title is not None: self.title = title
        if filename is not None: self.filename = filename
        if file_path is not None: self.file_path = file_path
        if file_type is not None: self.file_type = file_type
        if department is not None: self.department = department
        if owner_id is not None: self.owner_id = owner_id
        if owner is not None: self.owner = owner
        if classification is not None: self.classification = classification
        if allowed_roles is not None: self.allowed_roles = allowed_roles
        if allowed_departments is not None: self.allowed_departments = allowed_departments
        if sensitivity is not None: self.sensitivity = sensitivity
        if chunk_count is not None: self.chunk_count = chunk_count
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def allowed_roles(self):
        try:
            return json.loads(self.allowed_roles_json) if self.allowed_roles_json else []
        except Exception:
            return []

    @allowed_roles.setter
    def allowed_roles(self, val):
        if isinstance(val, list):
            self.allowed_roles_json = json.dumps(val)
        else:
            self.allowed_roles_json = json.dumps([str(val)])

    @property
    def allowed_departments(self):
        try:
            return json.loads(self.allowed_departments_json) if self.allowed_departments_json else ["ALL"]
        except Exception:
            return ["ALL"]

    @allowed_departments.setter
    def allowed_departments(self, val):
        if isinstance(val, list):
            self.allowed_departments_json = json.dumps(val)
        else:
            self.allowed_departments_json = json.dumps([str(val)])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'filename': self.filename,
            'file_type': self.file_type,
            'department': self.department,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else 'System',
            'classification': self.classification,
            'allowed_roles': self.allowed_roles,
            'allowed_departments': self.allowed_departments,
            'sensitivity': self.sensitivity,
            'chunk_count': self.chunk_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DocumentChunk(db.Model):
    __tablename__ = 'document_chunks'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    metadata_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, document_id=None, chunk_index=None, content=None, metadata_dict=None, metadata_json=None, **kwargs):
        super().__init__()
        if document_id is not None: self.document_id = document_id
        if chunk_index is not None: self.chunk_index = chunk_index
        if content is not None: self.content = content
        if metadata_dict is not None: self.metadata_dict = metadata_dict
        if metadata_json is not None: self.metadata_json = metadata_json
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def metadata_dict(self):
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @metadata_dict.setter
    def metadata_dict(self, val):
        self.metadata_json = json.dumps(val)
