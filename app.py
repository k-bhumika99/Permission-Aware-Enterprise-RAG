import os
from flask import Flask, render_template, g
from config import Config
from models import db
from models.user import User
from models.document import Document, DocumentChunk
from models.audit import AuditLog, QueryRecord

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.documents import documents_bp
from routes.rag import rag_bp
from routes.users import users_bp
from routes.permissions import permissions_bp
from routes.audit import audit_bp
from routes.security import security_bp
from routes.profile import profile_bp
from routes.settings import settings_bp

from services.auth_service import AuthService
from services.embedding_service import EmbeddingService
from services.retrieval_service import VectorStoreService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Initialize SQLAlchemy database
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(permissions_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)

    @app.before_request
    def load_authenticated_user():
        g.user = AuthService.get_current_user()

    @app.route('/')
    def index_view():
        return render_template('index.html')

    # Global 404 & 500 error handlers (No raw stack traces exposed to users)
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', public_content=None), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        import traceback
        print(f"[500 ERROR EXCEPTION] {e}")
        traceback.print_exc()
        return render_template('base.html', error=str(e)), 500

    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        # Seed initial demo users and documents
        seed_demo_data()

    return app


def seed_demo_data():
    """
    Populates initial demo users and sample enterprise documents with permission metadata
    if database is empty.
    """
    if User.query.count() > 0:
        print("[System] Demo database already initialized.")
        return

    print("[System] Seeding enterprise demo users & permission-aware documents...")

    demo_users = [
        {"name": "System Admin", "email": "admin@enterprise.com", "role": "ADMIN", "department": "Operations"},
        {"name": "HR Specialist", "email": "hr@enterprise.com", "role": "HR", "department": "HR"},
        {"name": "Engineering Manager", "email": "manager@enterprise.com", "role": "MANAGER", "department": "Engineering"},
        {"name": "Senior Software Engineer", "email": "engineer@enterprise.com", "role": "EMPLOYEE", "department": "Engineering"},
        {"name": "Marketing Specialist", "email": "marketing@enterprise.com", "role": "EMPLOYEE", "department": "Marketing"}
    ]

    created_users = {}
    for udata in demo_users:
        user = User(
            name=udata['name'],
            email=udata['email'],
            role=udata['role'],
            department=udata['department'],
            is_active=True
        )
        user.set_password("Password123!")
        db.session.add(user)
        db.session.flush()
        created_users[udata['email']] = user

    db.session.commit()

    admin_user = created_users['admin@enterprise.com']
    hr_user = created_users['hr@enterprise.com']

    sample_documents = [
        {
            "title": "Engineering Project Guidelines 2026",
            "filename": "engineering_project_guidelines.txt",
            "department": "Engineering",
            "classification": "INTERNAL",
            "owner": admin_user,
            "allowed_roles": ["ADMIN", "HR", "MANAGER", "EMPLOYEE"],
            "allowed_departments": ["ALL"],
            "sensitivity": "MEDIUM",
            "content": """Engineering Project Guidelines & Standards 2026:
All software engineering teams must strictly enforce unit testing coverage (>80%), peer code reviews on git pull requests, and automated CI/CD pipeline deployments.
Deployment approvals require a two-stage signoff: Stage 1 by the Technical Lead and Stage 2 by the Engineering Manager.
Emergency production hotfixes must be logged in the incident management dashboard within 30 minutes of deployment."""
        },
        {
            "title": "Engineering Salary Structure & Payroll 2026",
            "filename": "engineering_salary_structure.txt",
            "department": "Engineering",
            "classification": "RESTRICTED",
            "owner": hr_user,
            "allowed_roles": ["HR", "ADMIN"],
            "allowed_departments": ["HR", "Operations"],
            "sensitivity": "TOP_SECRET",
            "content": """Engineering Department Salary & Executive Compensation Structure 2026:
RESTRICTED CONFIDENTIAL DOCUMENT - FOR HR AND EXECUTIVE ACCESS ONLY.
Level L3 Software Engineer Base Salary Range: $110,000 - $140,000 + 10% annual bonus.
Level L4 Senior Software Engineer Base Salary Range: $150,000 - $190,000 + 15% equity target.
Level L5 Engineering Manager Base Salary Range: $195,000 - $240,000 + 25% performance bonus.
Executive Director Compensation: $350,000 base + stock options package."""
        },
        {
            "title": "HR Employee Onboarding & Benefits Policy",
            "filename": "hr_onboarding_policy.txt",
            "department": "HR",
            "classification": "CONFIDENTIAL",
            "owner": hr_user,
            "allowed_roles": ["HR", "MANAGER", "ADMIN"],
            "allowed_departments": ["HR", "ALL"],
            "sensitivity": "HIGH",
            "content": """Human Resources Onboarding & Benefits Policy 2026:
New employee onboarding must be completed within the first 5 business days.
Health insurance coverage initiates on the 1st of the month following enrollment.
401(k) company matching is 100% up to the first 4% of employee base compensation after 90 days of employment.
Annual leave allowance is 20 paid leave days plus official corporate holidays."""
        },
        {
            "title": "Company All-Hands Announcement & Roadmap",
            "filename": "company_all_hands.txt",
            "department": "Operations",
            "classification": "PUBLIC",
            "owner": admin_user,
            "allowed_roles": ["ADMIN", "HR", "MANAGER", "EMPLOYEE"],
            "allowed_departments": ["ALL"],
            "sensitivity": "LOW",
            "content": """Enterprise Global All-Hands Announcement 2026:
Welcome all team members to Q3! Our primary company targets focus on enterprise security, zero-trust RAG adoption, and global expansion.
All employees are invited to join the monthly townhall on the first Thursday of every month at 10 AM EST."""
        },
        {
            "title": "Marketing Q3 Campaign Strategy",
            "filename": "marketing_q3_strategy.txt",
            "department": "Marketing",
            "classification": "INTERNAL",
            "owner": admin_user,
            "allowed_roles": ["ADMIN", "HR", "MANAGER", "EMPLOYEE"],
            "allowed_departments": ["Marketing", "ALL"],
            "sensitivity": "MEDIUM",
            "content": """Marketing Department Q3 Strategy & Brand Positioning:
Our Q3 campaign centers on highlighting our zero-trust Permission-Aware Enterprise RAG platform.
Key target audiences include Enterprise CISOs, CTOs, and AI Security Architects."""
        }
    ]

    for doc_info in sample_documents:
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(Config.UPLOAD_FOLDER, doc_info["filename"])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(doc_info["content"])

        doc = Document(
            title=doc_info["title"],
            filename=doc_info["filename"],
            file_path=file_path,
            file_type="txt",
            department=doc_info["department"],
            owner_id=doc_info["owner"].id,
            classification=doc_info["classification"],
            allowed_roles=doc_info["allowed_roles"],
            allowed_departments=doc_info["allowed_departments"],
            sensitivity=doc_info["sensitivity"],
            chunk_count=1
        )
        db.session.add(doc)
        db.session.flush()

        metadata = {
            'document_id': doc.id,
            'title': doc.title,
            'department': doc.department,
            'classification': doc.classification,
            'allowed_roles': doc.allowed_roles,
            'allowed_departments': doc.allowed_departments,
            'owner_id': doc.owner_id,
            'chunk_index': 0
        }

        chunk_obj = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            content=doc_info["content"],
            metadata_dict=metadata
        )
        db.session.add(chunk_obj)
        db.session.flush()

        # Vector embedding & indexing
        embedding = EmbeddingService.get_embedding(doc_info["content"])
        VectorStoreService.add_chunk(
            chunk_id=chunk_obj.id,
            document_id=doc.id,
            content=doc_info["content"],
            embedding=embedding,
            metadata=metadata
        )

    db.session.commit()
    print("[System] Demo database and Permission Vector Store successfully initialized!")


app = create_app()

if __name__ == '__main__':
    print("==================================================")
    print("[System] Permission-Aware Enterprise RAG Engine Starting...")
    print("[Server] Local Web App URL: http://127.0.0.1:5000")
    print("==================================================")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
