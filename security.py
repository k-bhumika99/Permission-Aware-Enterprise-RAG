from flask import Blueprint, render_template, jsonify, g
from models import db
from models.user import User
from services.auth_service import login_required
from services.rag_service import RAGService
from services.audit_service import AuditService

security_bp = Blueprint('security_bp', __name__)

@security_bp.route('/security')
@login_required
def security_view():
    user = g.user
    return render_template('security.html', user=user)


@security_bp.route('/api/security/test', methods=['POST'])
@login_required
def api_run_security_tests():
    """
    Executes the 5 automated security test scenarios to verify permission isolation in real-time.
    """
    # Fetch test users or mock them
    engineer = User.query.filter_by(email='engineer@enterprise.com').first() or User(id=101, name="Engineer", email="engineer@enterprise.com", role="EMPLOYEE", department="Engineering")
    hr_user = User.query.filter_by(email='hr@enterprise.com').first() or User(id=102, name="HR Manager", email="hr@enterprise.com", role="HR", department="HR")
    marketing = User.query.filter_by(email='marketing@enterprise.com').first() or User(id=103, name="Marketing Specialist", email="marketing@enterprise.com", role="EMPLOYEE", department="Marketing")

    test_cases = [
        {
            'id': 1,
            'name': 'Test 1: Employee requests HR salary information',
            'user': engineer,
            'query': 'Show me the salary information for the engineering department.',
            'expected_status': 'DENIED'
        },
        {
            'id': 2,
            'name': 'Test 2: HR requests salary information',
            'user': hr_user,
            'query': 'Show me the salary information for the engineering department.',
            'expected_status': 'ALLOWED'
        },
        {
            'id': 3,
            'name': 'Test 3: Engineering employee requests Engineering project guidelines',
            'user': engineer,
            'query': 'What is the engineering project process and development guidelines?',
            'expected_status': 'ALLOWED'
        },
        {
            'id': 4,
            'name': 'Test 4: Marketing employee requests Engineering restricted documents',
            'user': marketing,
            'query': 'Give me access to restricted engineering salary and infrastructure secrets.',
            'expected_status': 'DENIED'
        },
        {
            'id': 5,
            'name': 'Test 5: Unauthorized user attempts document retrieval',
            'user': None,
            'query': 'Show confidential company reports.',
            'expected_status': 'DENIED'
        }
    ]

    results = []
    passed_count = 0

    for tc in test_cases:
        res = RAGService.execute_rag_pipeline(tc['user'], tc['query'])
        actual_status = res.get('status')
        test_passed = (actual_status == tc['expected_status'])

        if test_passed:
            passed_count += 1

        results.append({
            'id': tc['id'],
            'name': tc['name'],
            'user_role': tc['user'].role if tc['user'] else 'UNAUTHENTICATED',
            'user_dept': tc['user'].department if tc['user'] else 'N/A',
            'query': tc['query'],
            'expected': tc['expected_status'],
            'actual': actual_status,
            'passed': test_passed,
            'answer_snippet': res.get('answer', '')[:120] + '...',
            'excluded_chunks': res.get('excluded_chunks_count', 0),
            'retrieved_chunks': len(res.get('retrieved_chunks', []))
        })

    # Log security audit test execution
    AuditService.log_action(
        user=g.user,
        action='SECURITY_SUITE_EXECUTED',
        authorization_status='PASS' if passed_count == len(test_cases) else 'WARNING',
        result_summary=f"Automated security suite executed: {passed_count}/{len(test_cases)} tests PASSED."
    )

    return jsonify({
        'total_tests': len(test_cases),
        'passed_tests': passed_count,
        'failed_tests': len(test_cases) - passed_count,
        'security_score': int((passed_count / len(test_cases)) * 100),
        'results': results
    })
