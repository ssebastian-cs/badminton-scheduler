from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import desc
from ..models import Comment, User, db
from ..forms import CommentForm
from ..security import rate_limit_endpoint, csrf_protect_ajax, log_security_event, sanitize_form_data

comments_bp = Blueprint('comments', __name__)


@comments_bp.route('/comments')
@login_required
def comments():
    """Display all comments with author and timestamp information."""
    # Get all comments using optimized query
    from ..db_queries import OptimizedQueries
    all_comments = OptimizedQueries.get_recent_comments(100)  # Get last 100 comments
    
    # Create a new comment form
    form = CommentForm()
    
    return render_template('comments_bootstrap.html', comments=all_comments, form=form)


@comments_bp.route('/comments/add', methods=['POST'])
@login_required
@rate_limit_endpoint(max_requests=15, window_minutes=10, per_user=True)
def add_comment():
    """Add new comment with content validation."""
    form = CommentForm()
    
    if form.validate_on_submit():
        try:
            # Create new comment
            comment = Comment(
                user_id=current_user.id,
                content=form.content.data.strip()
            )
            
            db.session.add(comment)
            db.session.commit()
            
            # Invalidate comment cache
            from ..db_queries import CacheManager
            CacheManager.invalidate_comment_cache(current_user.id)
            
            flash('Comment posted successfully!', 'success')
        except ValueError as e:
            flash(f'Error posting comment: {str(e)}', 'error')
            db.session.rollback()
        except Exception as e:
            flash('An error occurred while posting your comment. Please try again.', 'error')
            db.session.rollback()
    else:
        # Display form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')
    
    return redirect(url_for('comments.comments'))


@comments_bp.route('/comments/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    """Edit comment with ownership validation (own comments only, except admin)."""
    comment = Comment.query.get_or_404(comment_id)
    
    # Check ownership - users can only edit their own comments, except admins
    if not current_user.is_admin() and comment.user_id != current_user.id:
        flash('You can only edit your own comments.', 'error')
        return redirect(url_for('comments.comments'))
    
    form = CommentForm()
    
    if request.method == 'GET':
        # Pre-populate form with existing comment content
        form.content.data = comment.content
    
    if form.validate_on_submit():
        try:
            # Update comment content
            comment.update_content(form.content.data.strip())
            db.session.commit()
            
            flash('Comment updated successfully!', 'success')
            return redirect(url_for('comments.comments'))
        except ValueError as e:
            flash(f'Error updating comment: {str(e)}', 'error')
            db.session.rollback()
        except Exception as e:
            flash('An error occurred while updating your comment. Please try again.', 'error')
            db.session.rollback()
    
    return render_template('comments/edit_comment_bootstrap.html', form=form, comment=comment)


@comments_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Delete comment with proper authorization (own comments only, except admin)."""
    comment = Comment.query.get_or_404(comment_id)
    
    # Check ownership - users can only delete their own comments, except admins
    if not current_user.is_admin() and comment.user_id != current_user.id:
        flash('You can only delete your own comments.', 'error')
        return redirect(url_for('comments.comments'))
    
    try:
        # Store comment info for flash message
        comment_author = comment.user.username
        is_own_comment = comment.user_id == current_user.id
        
        db.session.delete(comment)
        db.session.commit()
        
        if is_own_comment:
            flash('Your comment has been deleted.', 'success')
        else:
            flash(f'Comment by {comment_author} has been deleted.', 'success')
    except Exception as e:
        flash('An error occurred while deleting the comment. Please try again.', 'error')
        db.session.rollback()
    
    return redirect(url_for('comments.comments'))


@comments_bp.route('/api/comments/<int:comment_id>/delete', methods=['DELETE'])
@login_required
@csrf_protect_ajax()
@rate_limit_endpoint(max_requests=10, window_minutes=10, per_user=True)
def api_delete_comment(comment_id):
    """API endpoint for deleting comments (for AJAX requests)."""
    comment = Comment.query.get_or_404(comment_id)
    
    # Check ownership - users can only delete their own comments, except admins
    if not current_user.is_admin() and comment.user_id != current_user.id:
        return jsonify({'error': 'You can only delete your own comments.'}), 403
    
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Comment deleted successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while deleting the comment.'}), 500