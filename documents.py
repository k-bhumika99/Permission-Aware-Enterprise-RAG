from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from models import db
from models.document import Document
from services.auth_service import login_required
from services.permission_service import PermissionService
from services.document_service import DocumentService
from services.retrieval_service import VectorStoreService
from services.audit_service import AuditService

documents_bp = Blueprint('documents_bp', __name__)

@documents_bp.route('/documents')
@login_required
def documents_view():
    user = g.user
    all_docs = Document.query.order_by(Document.created_at.desc()).all()
    
    # Filter documents based on permissions unless admin wants to see all with labels
    user_authorized_docs = PermissionService.filter_authorized_documents(user, all_docs)
    
    doc_data = []
    for d in all_docs:
        can_access, reason = PermissionService.can_access_document(user, d)
        doc_data.append({
            'doc': d,
            'can_access': can_access,
            'access_reason': reason
        })

    return render_template('documents.html', user=user, doc_data=doc_data, authorized_count=len(user_authorized_docs))


@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_view():
    user = g.user
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        department = request.form.get('department', user.department)
        classification = request.form.get('classification', 'INTERNAL')
        allowed_roles = request.form.getlist('allowed_roles') or ['ADMIN', 'HR', 'MANAGER', 'EMPLOYEE']
        allowed_departments = request.form.getlist('allowed_departments') or ['ALL']
        sensitivity = request.form.get('sensitivity', 'MEDIUM')
        file_obj = request.files.get('file')

        if not title or not file_obj or not file_obj.filename:
            flash('Please provide a document title and select a valid file.', 'danger')
            return render_template('upload.html', user=user)

        if not DocumentService.allowed_file(file_obj.filename):
            flash('Unsupported file format. Allowed: PDF, TXT, DOCX, MD.', 'danger')
            return render_template('upload.html', user=user)

        try:
            doc, msg = DocumentService.process_and_index_document(
                title=title,
                file_obj=file_obj,
                department=department,
                classification=classification,
                allowed_roles=allowed_roles,
                allowed_departments=allowed_departments,
                owner=user,
                sensitivity=sensitivity
            )

            AuditService.log_action(
                user=user,
                action='DOCUMENT_UPLOAD',
                document_id=doc.id,
                authorization_status='PASS',
                result_summary=f"Uploaded document '{title}' ({classification}) with {doc.chunk_count} chunks indexed."
            )

            flash(f"Document '{title}' successfully uploaded and indexed into Permission Vector Store!", 'success')
            return redirect(url_for('documents_bp.documents_view'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error processing document upload: {str(e)}", 'danger')
            return render_template('upload.html', user=user)

    return render_template('upload.html', user=user)


@documents_bp.route('/api/documents', methods=['GET'])
@login_required
def api_list_documents():
    user = g.user
    all_docs = Document.query.all()
    authorized = PermissionService.filter_authorized_documents(user, all_docs)
    return jsonify({
        'total': len(all_docs),
        'authorized_count': len(authorized),
        'documents': [d.to_dict() for d in authorized]
    })


@documents_bp.route('/api/documents/<int:doc_id>', methods=['GET'])
@login_required
def api_get_document(doc_id):
    user = g.user
    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    can_access, reason = PermissionService.can_access_document(user, doc)
    if not can_access:
        AuditService.log_action(
            user=user,
            action='DOCUMENT_ACCESS',
            document_id=doc.id,
            authorization_status='DENIED',
            result_summary=f"Unauthorized access attempt to document #{doc.id}: {reason}"
        )
        return jsonify({'error': 'Access Denied', 'reason': reason}), 403

    AuditService.log_action(
        user=user,
        action='DOCUMENT_ACCESS',
        document_id=doc.id,
        authorization_status='ALLOWED',
        result_summary=f"Accessed document #{doc.id}: {doc.title}"
    )

    return jsonify({'document': doc.to_dict(), 'chunks': [c.metadata_dict for c in doc.chunks]})


@documents_bp.route('/api/documents/<int:doc_id>/delete', methods=['POST', 'DELETE'])
@login_required
def api_delete_document(doc_id):
    user = g.user
    doc = db.session.get(Document, doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    if user.role != 'ADMIN' and doc.owner_id != user.id:
        return jsonify({'error': 'Permission Denied: Only ADMIN or document owner can delete this document.'}), 403

    title = doc.title
    # Delete chunks from vector store
    VectorStoreService.delete_document_chunks(doc.id)

    db.session.delete(doc)
    db.session.commit()

    AuditService.log_action(
        user=user,
        action='DOCUMENT_DELETE',
        document_id=doc_id,
        authorization_status='PASS',
        result_summary=f"Deleted document #{doc_id} ('{title}') and removed vector index entries."
    )

    return jsonify({'message': f"Document '{title}' deleted successfully."})
