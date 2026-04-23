from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Complaint, Comment
from ml.categorizer import classifier, predict_department

complaints = Blueprint('complaints', __name__)

@complaints.route('/portal')
@login_required
def portal():
    all_c = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    total = len(all_c)
    open_count = sum(1 for c in all_c if c.status == 'Open')
    in_progress = sum(1 for c in all_c if c.status == 'In Progress')
    resolved = sum(1 for c in all_c if c.status == 'Resolved')
    recent = all_c[:5]
    # Pie chart data
    status_data = {'Open': open_count, 'In Progress': in_progress,
                   'Resolved': resolved,
                   'Closed': sum(1 for c in all_c if c.status == 'Closed')}
    return render_template('portal.html', total=total, open_count=open_count,
        in_progress=in_progress, resolved=resolved, recent=recent, status_data=status_data)

@complaints.route('/dashboard')
@login_required
def dashboard():
    query = Complaint.query.filter_by(user_id=current_user.id)
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    priority_filter = request.args.get('priority', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search:
        query = query.filter(Complaint.title.ilike(f'%{search}%'))
    if sort == 'oldest':
        query = query.order_by(Complaint.created_at.asc())
    else:
        query = query.order_by(Complaint.created_at.desc())
    user_complaints = query.all()
    return render_template('dashboard.html', complaints=user_complaints,
        status_filter=status_filter, category_filter=category_filter,
        priority_filter=priority_filter, search=search, sort=sort)

@complaints.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        combined_text = f"{title} {description}"
        category = classifier.predict_category(combined_text)
        priority = classifier.predict_priority(combined_text)
        department = predict_department(combined_text)
        complaint = Complaint(
            title=title, description=description,
            category=category, priority=priority,
            assigned_to=department,
            user_id=current_user.id
        )
        db.session.add(complaint)
        db.session.commit()
        flash(f'Complaint submitted. Priority: {priority} | Assigned to: {department}', 'success')
        return redirect(url_for('complaints.dashboard'))
    return render_template('submit.html')

@complaints.route('/complaint/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def view(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.user_id != current_user.id and current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('complaints.dashboard'))
    if request.method == 'POST':
        text = request.form.get('comment')
        if text:
            comment = Comment(text=text, author=current_user.name, complaint_id=complaint.id)
            db.session.add(comment)
            db.session.commit()
            flash('Comment added.', 'success')
        return redirect(url_for('complaints.view', complaint_id=complaint_id))
    return render_template('view_complaint.html', complaint=complaint)

@complaints.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from models import User
    from werkzeug.security import generate_password_hash, check_password_hash
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        new_password = request.form.get('new_password')
        current_password = request.form.get('current_password')
        if new_password:
            if not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('complaints.profile'))
            current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('complaints.profile'))
    total = Complaint.query.filter_by(user_id=current_user.id).count()
    resolved = Complaint.query.filter_by(user_id=current_user.id, status='Resolved').count()
    return render_template('profile.html', total=total, resolved=resolved)
