from flask import Blueprint, render_template, redirect, url_for, flash, request, g
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from ..models import User, db
from ..forms import LoginForm, RegistrationForm
from ..security import SecurityValidator, log_security_event, sanitize_form_data

auth_bp = Blueprint('auth', __name__)


def admin_required(f):
    """Decorator to require admin role for route access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('availability.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route with comprehensive security and rate limiting."""
    if current_user.is_authenticated:
        return redirect(url_for('availability.dashboard'))
    
    # Get client IP for rate limiting
    client_ip = g.get('client_ip', request.remote_addr)
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Check if IP is rate limited for login attempts
        from ..security import rate_limiter
        is_limited, remaining, lockout_time = rate_limiter.is_login_rate_limited(
            client_ip, max_attempts=3, window_minutes=15
        )
        
        if is_limited:
            log_security_event('LOGIN_RATE_LIMITED', 
                             f'IP {client_ip} exceeded login attempts', 'WARNING')
            flash('Too many failed login attempts. Please try again later.', 'error')
            return render_template('auth/login_bootstrap.html', form=form)
        
        # Check if username is rate limited
        username_limited, _, _ = rate_limiter.is_login_rate_limited(
            f"user_{username}", max_attempts=5, window_minutes=30
        )
        
        if username_limited:
            log_security_event('USERNAME_RATE_LIMITED', 
                             f'Username {username} exceeded login attempts', 'WARNING')
            flash('Too many failed attempts for this account. Please try again later.', 'error')
            return render_template('auth/login_bootstrap.html', form=form)
        
        # Check if account is locked
        is_locked, unlock_time = rate_limiter.is_account_locked(username)
        if is_locked:
            log_security_event('ACCOUNT_LOCKED_ACCESS', 
                             f'Attempt to access locked account: {username}', 'WARNING')
            flash('This account is temporarily locked. Please try again later.', 'error')
            return render_template('auth/login_bootstrap.html', form=form)
        
        # Additional security validation
        username_valid, username_error = SecurityValidator.validate_username(username)
        if not username_valid:
            rate_limiter.record_login_attempt(client_ip, success=False)
            rate_limiter.record_login_attempt(f"user_{username}", success=False)
            flash('Invalid username or password.', 'error')
            return render_template('auth/login_bootstrap.html', form=form)
        
        # Sanitize form data
        try:
            sanitized_data = sanitize_form_data({
                'username': username,
                'password': password
            })
        except Exception as e:
            rate_limiter.record_login_attempt(client_ip, success=False)
            rate_limiter.record_login_attempt(f"user_{username}", success=False)
            log_security_event('FORM_SANITIZATION_FAILED', 
                             f'Failed to sanitize login form: {str(e)}', 'ERROR')
            flash('Invalid request. Please try again.', 'error')
            return render_template('auth/login_bootstrap.html', form=form)
        
        user = User.query.filter_by(username=sanitized_data['username']).first()
        
        if user and user.check_password(sanitized_data['password']):
            if not user.is_active:
                rate_limiter.record_login_attempt(client_ip, success=False)
                rate_limiter.record_login_attempt(f"user_{username}", success=False)
                log_security_event('BLOCKED_ACCOUNT_LOGIN', 
                                 f'Login attempt to blocked account: {username}', 'WARNING')
                flash('Your account has been blocked. Please contact an administrator.', 'error')
                return render_template('auth/login_bootstrap.html', form=form)
            
            # Successful login - clear rate limiting
            rate_limiter.record_login_attempt(client_ip, success=True)
            rate_limiter.record_login_attempt(f"user_{username}", success=True)
            
            login_user(user, remember=False)
            log_security_event('SUCCESSFUL_LOGIN', 
                             f'User {username} logged in successfully', 'INFO')
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Validate and sanitize next page parameter
            next_page = request.args.get('next')
            if next_page:
                # Security check for next page parameter
                if next_page.startswith('/') and not next_page.startswith('//'):
                    # Additional validation for next parameter
                    if not any(dangerous in next_page.lower() for dangerous in ['javascript:', 'data:', 'vbscript:']):
                        return redirect(next_page)
            
            return redirect(url_for('availability.dashboard'))
        else:
            # Failed login - record attempt
            rate_limiter.record_login_attempt(client_ip, success=False)
            rate_limiter.record_login_attempt(f"user_{username}", success=False)
            
            log_security_event('FAILED_LOGIN', 
                             f'Failed login attempt for username: {username}', 'WARNING')
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login_bootstrap.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    """User registration route (Admin only) - redirects to admin create user."""
    # Redirect to the new admin create user route
    return redirect(url_for('admin.create_user'))


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route with aggressive session cleanup."""
    username = current_user.username
    
    # Clear the session
    logout_user()
    
    # Clear any additional session data
    from flask import session
    session.clear()
    
    # Create response with redirect
    response = redirect(url_for('auth.login'))
    
    # Clear session cookies aggressively
    response.set_cookie('session', '', expires=0, path='/')
    response.set_cookie('remember_token', '', expires=0, path='/')
    
    # Add cache control headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    flash(f'You have been logged out successfully, {username}.', 'info')
    return response