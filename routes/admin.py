from flask import Blueprint, render_template, redirect, url_for, request, flash, Response
from flask_login import login_required, current_user
from models import db, Complaint, User
from functools import wraps
import csv, io

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('complaints.dashboard'))
        return f(*args, **kwargs)
    return decorated

@admin.route('/admin')
@login_required
@admin_required
def dashboard():
    query = Complaint.query
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    search = request.args.get('search', '')
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)
    if search:
        query = query.filter(Complaint.title.ilike(f'%{search}%'))
    all_complaints = query.order_by(Complaint.created_at.desc()).all()

    total = Complaint.query.count()
    open_count = Complaint.query.filter_by(status='Open').count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    high_priority = Complaint.query.filter_by(priority='High').count()

    categories = {}
    statuses = {}
    for c in Complaint.query.all():
        categories[c.category] = categories.get(c.category, 0) + 1
        statuses[c.status] = statuses.get(c.status, 0) + 1

    return render_template('admin.html',
        complaints=all_complaints, total=total,
        open_count=open_count, resolved=resolved,
        high_priority=high_priority, categories=categories, statuses=statuses,
        status_filter=status_filter, category_filter=category_filter, search=search
    )

@admin.route('/admin/update/<int:complaint_id>', methods=['POST'])
@login_required
@admin_required
def update(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = request.form.get('status', complaint.status)
    complaint.resolution_note = request.form.get('resolution_note', '')
    complaint.priority = request.form.get('priority', complaint.priority)
    complaint.assigned_to = request.form.get('assigned_to', complaint.assigned_to)
    db.session.commit()
    flash('Complaint updated.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/export')
@login_required
@admin_required
def export_csv():
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'User', 'Title', 'Category', 'Priority', 'Status', 'Submitted', 'Resolution Note'])
    for c in complaints:
        writer.writerow([c.id, c.user.name, c.title, c.category, c.priority,
                         c.status, c.created_at.strftime('%d-%m-%Y'), c.resolution_note])
    output.seek(0)
    return Response(output, mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=complaints.csv'})
