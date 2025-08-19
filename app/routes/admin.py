from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from ..routes.auth import admin_required
from ..models import User, Availability, Comment, AdminAction, db
from ..forms import RegistrationForm, AvailabilityForm, CommentForm
from ..utils import log_admin_action, get_admin_actions
from ..error_tracking import get_error_summary, get_error_report
from ..security import rate_limit_endpoint, log_security_event
from datetime import date, datetime

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with user management interface and recent actions."""
    # Get statistics using optimized queries
    from ..db_queries import OptimizedQueries
    user_stats = OptimizedQueries.get_user_statistics()
    content_stats = OptimizedQueries.get_content_statistics()
    
    # Combine statistics
    stats = {**user_stats, **content_stats}
    
    # Get recent admin actions for audit trail using optimized queries
    recent_actions = OptimizedQueries.get_recent_admin_actions(10)
    
    return render_template('admin_dashboard_bootstrap.html', stats=stats, recent_actions=recent_actions)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management interface with all users listed."""
    # Get all users with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Show 20 users per page
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin_users_bootstrap.html', users=users)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
@rate_limit_endpoint(max_requests=15, window_minutes=10, per_user=True)
def create_user():
    """Create new user functionality (admin only)."""
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                password=form.password.data,
                role=form.role.data
            )
            db.session.add(user)
            db.session.commit()
            
            # Log admin action
            log_admin_action(
                action_type='create_user',
                target_type='user',
                target_id=user.id,
                details={
                    'username': user.username,
                    'role': user.role,
                    'description': f'Created user {user.username} with role {user.role}'
                }
            )
            
            flash(f'User {user.username} created successfully with role {user.role}.', 'success')
            return redirect(url_for('admin.users'))
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the user. Please try again.', 'error')
    else:
        # Display form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.title()}: {error}', 'error')
    
    return render_template('admin/create_user.html', form=form)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
@rate_limit_endpoint(max_requests=20, window_minutes=5, per_user=True)
def toggle_user_status(user_id):
    """Block/unblock user system."""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from blocking themselves
    if user.id == current_user.id:
        flash('You cannot block your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    # Prevent blocking the last admin
    if user.is_admin() and user.is_active:
        active_admins = User.query.filter_by(role='Admin', is_active=True).count()
        # If blocking this admin would leave 0 or fewer active admins, prevent it
        # We need at least 1 admin to remain active, so prevent blocking if there's only 1 active admin
        if active_admins <= 1:
            flash('Cannot block the last active admin', 'error')
            return redirect(url_for('admin.users'))
    
    try:
        old_status = user.is_active
        user.is_active = not user.is_active
        db.session.commit()
        
        # Log admin action
        action_type = 'unblock_user' if user.is_active else 'block_user'
        status = "unblocked" if user.is_active else "blocked"
        log_admin_action(
            action_type=action_type,
            target_type='user',
            target_id=user.id,
            details={
                'previous_status': old_status, 
                'new_status': user.is_active,
                'description': f'{status.capitalize()} user {user.username}'
            }
        )
        
        flash(f'User {user.username} has been {status} successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating user status. Please try again.', 'error')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
@rate_limit_endpoint(max_requests=10, window_minutes=10, per_user=True)
def delete_user(user_id):
    """Delete user functionality with data cleanup."""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    # Prevent deleting the last admin
    if user.is_admin():
        admin_count = User.query.filter_by(role='Admin').count()
        if admin_count <= 1:
            flash('Cannot delete the last admin user.', 'error')
            return redirect(url_for('admin.users'))
    
    try:
        username = user.username
        user_id_for_log = user.id
        
        # Log admin action before deletion
        log_admin_action(
            action_type='delete_user',
            target_type='user',
            target_id=user_id_for_log,
            details={
                'username': username, 
                'role': user.role,
                'description': f'Deleted user {username}'
            }
        )
        
        # The cascade='all, delete-orphan' in the model relationships will handle cleanup
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} and all associated data have been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the user: {str(e)}', 'error')
        print(f"Delete user error: {e}")  # Debug logging
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View detailed user information."""
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    availability_count = len(user.availability_entries)
    comment_count = len(user.comments)
    
    user_stats = {
        'availability_count': availability_count,
        'comment_count': comment_count
    }
    
    return render_template('admin/user_detail.html', user=user, stats=user_stats)

@admin_bp.route('/availability')
@login_required
@admin_required
def manage_availability():
    """Admin interface for managing all users' availability entries."""
    # Get filter parameters
    user_filter = request.args.get('user_id', type=int)
    date_filter = request.args.get('date')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = Availability.query.join(User)
    
    if user_filter:
        query = query.filter(Availability.user_id == user_filter)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Availability.date == filter_date)
        except ValueError:
            flash('Invalid date format.', 'error')
    
    # Order by date and paginate
    availability_entries = query.order_by(Availability.date.desc(), Availability.start_time).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get all users for filter dropdown
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    return render_template('admin/manage_availability.html', 
                         availability_entries=availability_entries,
                         users=users,
                         user_filter=user_filter,
                         date_filter=date_filter)


@admin_bp.route('/availability/<int:availability_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_availability(availability_id):
    """Admin interface for editing any user's availability."""
    availability = Availability.query.get_or_404(availability_id)
    form = AvailabilityForm(obj=availability)
    
    if form.validate_on_submit():
        try:
            # Store original values for audit log
            original_data = {
                'date': availability.date.isoformat(),
                'start_time': availability.start_time.strftime('%H:%M'),
                'end_time': availability.end_time.strftime('%H:%M')
            }
            
            # Update availability
            availability.update(
                date=form.date.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data
            )
            db.session.commit()
            
            # Log admin action
            log_admin_action(
                action_type='edit_availability',
                target_type='availability',
                target_id=availability.id,
                details={
                    'user_id': availability.user_id,
                    'username': availability.user.username,
                    'description': f'Edited availability for {availability.user.username} on {form.date.data}',
                    'original': original_data,
                    'new': {
                        'date': form.date.data.isoformat(),
                        'start_time': form.start_time.data.strftime('%H:%M'),
                        'end_time': form.end_time.data.strftime('%H:%M')
                    }
                }
            )
            
            flash(f'Availability for {availability.user.username} updated successfully!', 'success')
            return redirect(url_for('admin.manage_availability'))
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating availability.', 'error')
    
    return render_template('admin/edit_availability.html', form=form, availability=availability)


@admin_bp.route('/availability/<int:availability_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_availability(availability_id):
    """Admin interface for deleting any user's availability."""
    availability = Availability.query.get_or_404(availability_id)
    
    try:
        # Store info for audit log
        user_username = availability.user.username
        availability_date = availability.date
        
        # Log admin action before deletion
        log_admin_action(
            action_type='delete_availability',
            target_type='availability',
            target_id=availability.id,
            details={
                'user_id': availability.user_id,
                'username': user_username,
                'description': f'Deleted availability for {user_username} on {availability_date}',
                'date': availability.date.isoformat(),
                'start_time': availability.start_time.strftime('%H:%M'),
                'end_time': availability.end_time.strftime('%H:%M')
            }
        )
        
        db.session.delete(availability)
        db.session.commit()
        
        flash(f'Availability for {user_username} on {availability_date} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting availability.', 'error')
    
    return redirect(url_for('admin.manage_availability'))


@admin_bp.route('/comments')
@login_required
@admin_required
def manage_comments():
    """Admin interface for managing all comments."""
    # Get filter parameters
    user_filter = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = Comment.query.join(User)
    
    if user_filter:
        query = query.filter(Comment.user_id == user_filter)
    
    # Order by creation date and paginate
    comments = query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get all users for filter dropdown
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    return render_template('admin/manage_comments.html', 
                         comments=comments,
                         users=users,
                         user_filter=user_filter)


@admin_bp.route('/comments/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_comment(comment_id):
    """Admin interface for editing any user's comment."""
    comment = Comment.query.get_or_404(comment_id)
    form = CommentForm()
    
    if request.method == 'GET':
        form.content.data = comment.content
    
    if form.validate_on_submit():
        try:
            # Store original content for audit log
            original_content = comment.content
            
            # Update comment
            comment.update_content(form.content.data.strip())
            db.session.commit()
            
            # Log admin action
            log_admin_action(
                action_type='edit_comment',
                target_type='comment',
                target_id=comment.id,
                details={
                    'user_id': comment.user_id,
                    'username': comment.user.username,
                    'description': f'Edited comment by {comment.user.username}',
                    'original_content': original_content[:100] + '...' if len(original_content) > 100 else original_content,
                    'new_content': form.content.data[:100] + '...' if len(form.content.data) > 100 else form.content.data
                }
            )
            
            flash(f'Comment by {comment.user.username} updated successfully!', 'success')
            return redirect(url_for('admin.manage_comments'))
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the comment.', 'error')
    
    return render_template('admin/edit_comment.html', form=form, comment=comment)


@admin_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_comment(comment_id):
    """Admin interface for deleting any user's comment."""
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        # Store info for audit log
        user_username = comment.user.username
        content_preview = comment.content[:100] + '...' if len(comment.content) > 100 else comment.content
        
        # Log admin action before deletion
        log_admin_action(
            action_type='delete_comment',
            target_type='comment',
            target_id=comment.id,
            details={
                'user_id': comment.user_id,
                'username': user_username,
                'description': f'Deleted comment by {user_username}',
                'content': content_preview,
                'created_at': comment.created_at.isoformat()
            }
        )
        
        db.session.delete(comment)
        db.session.commit()
        
        flash(f'Comment by {user_username} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the comment.', 'error')
    
    return redirect(url_for('admin.manage_comments'))


@admin_bp.route('/audit')
@login_required
@admin_required
def audit_log():
    """Admin audit log showing all administrative actions."""
    # Get filter parameters
    action_type = request.args.get('action_type')
    target_type = request.args.get('target_type')
    admin_user_id = request.args.get('admin_user_id', type=int)
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = AdminAction.query.join(AdminAction.admin_user)
    
    if action_type:
        query = query.filter(AdminAction.action_type == action_type)
    
    if target_type:
        query = query.filter(AdminAction.target_type == target_type)
    
    if admin_user_id:
        query = query.filter(AdminAction.admin_user_id == admin_user_id)
    
    # Order by creation date and paginate
    actions = query.order_by(AdminAction.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get admin users for filter dropdown
    admin_users = User.query.filter_by(role='Admin').order_by(User.username).all()
    
    # Define filter options
    action_types = [
        'create_user', 'block_user', 'unblock_user', 'delete_user',
        'edit_availability', 'delete_availability',
        'edit_comment', 'delete_comment'
    ]
    
    target_types = ['user', 'availability', 'comment']
    
    return render_template('admin/audit_log.html',
                         actions=actions,
                         admin_users=admin_users,
                         action_types=action_types,
                         target_types=target_types,
                         current_filters={
                             'action_type': action_type,
                             'target_type': target_type,
                             'admin_user_id': admin_user_id
                         })


@admin_bp.route('/errors')
@login_required
@admin_required
def error_dashboard():
    """Admin error monitoring dashboard."""
    # Get time period from query params (default 24 hours)
    hours = request.args.get('hours', 24, type=int)
    
    # Get error summary and report
    error_summary = get_error_summary(hours)
    error_report = get_error_report(hours)
    
    return render_template('admin/error_dashboard.html', 
                         error_summary=error_summary,
                         error_report=error_report,
                         hours=hours)


@admin_bp.route('/errors/api')
@login_required
@admin_required
def error_api():
    """API endpoint for error data (for AJAX updates)."""
    hours = request.args.get('hours', 24, type=int)
    error_summary = get_error_summary(hours)
    return jsonify(error_summary)


@admin_bp.route('/errors/export')
@login_required
@admin_required
def export_errors():
    """Export error data as JSON."""
    from ..error_tracking import error_tracker
    hours = request.args.get('hours', 24, type=int)
    
    # Log admin action
    log_admin_action(
        action_type='export_errors',
        target_type='system',
        target_id=0,
        details={
            'hours': hours,
            'description': f'Exported error data for last {hours} hours'
        }
    )
    
    error_data = error_tracker.export_error_data(hours)
    
    response = jsonify(error_data)
    response.headers['Content-Disposition'] = f'attachment; filename=error_report_{hours}h.json'
    return response