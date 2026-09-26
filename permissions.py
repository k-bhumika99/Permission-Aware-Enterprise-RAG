from flask import Blueprint, render_template, jsonify, g
from models.user import User
from models.document import Document
from services.auth_service import login_required
from services.permission_service import PermissionService

permissions_bp = Blueprint('permissions_bp', __name__)

@permissions_bp.route('/permissions')
@login_required
def permissions_view():
    user = g.user
    documents = Document.query.order_by(Document.department, Document.title).all()

    # Construct mock role objects to render the exact role permissions matrix
    roles = ['EMPLOYEE', 'MANAGER', 'HR', 'ADMIN']
    matrix = []

    for doc in documents:
        role_access = {}
        for role in roles:
            # Create transient mock user for permission check
            mock_user = User(
                id=9999,
                name=f"Mock {role}",
                email=f"mock_{role.lower()}@test.com",
                role=role,
                department=doc.department # Test department alignment
            )
            allowed, reason = PermissionService.can_access_document(mock_user, doc)
            role_access[role] = {
                'allowed': allowed,
                'reason': reason
            }

        matrix.append({
            'document': doc,
            'role_access': role_access
        })

    return render_template('permissions.html', user=user, matrix=matrix, roles=roles)


@permissions_bp.route('/api/permissions/matrix')
@login_required
def api_permission_matrix():
    documents = Document.query.all()
    roles = ['EMPLOYEE', 'MANAGER', 'HR', 'ADMIN']
    res = []

    for doc in documents:
        access_map = {}
        for r in roles:
            mock_u = User(id=999, name=r, email=f"{r}@test.com", role=r, department=doc.department)
            allowed, _ = PermissionService.can_access_document(mock_u, doc)
            access_map[r] = allowed

        res.append({
            'document_id': doc.id,
            'title': doc.title,
            'department': doc.department,
            'classification': doc.classification,
            'access': access_map
        })

    return jsonify({'matrix': res})
