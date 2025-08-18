from app import create_app
from app.forms import CommentForm

app = create_app('testing')
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    with app.test_request_context():
        # Test security validation
        malicious_contents = [
            '<script>alert("xss")</script>',
            'javascript:alert(1)',
            '<img src=x onerror=alert(1)>',
            'onclick=alert(1)',
            'onload=alert(1)'
        ]
        
        for malicious_content in malicious_contents:
            form_data = {
                'content': malicious_content,
                'csrf_token': 'test_token'
            }
            form = CommentForm(data=form_data)
            is_valid = form.validate()
            print(f'Content: {malicious_content}')
            print(f'Valid: {is_valid}')
            print(f'Errors: {form.content.errors}')
            print('---')
        
        # Test empty content
        print("\nTesting empty content:")
        form_data = {
            'content': '',
            'csrf_token': 'test_token'
        }
        form = CommentForm(data=form_data)
        is_valid = form.validate()
        print(f'Empty string - Valid: {is_valid}')
        print(f'Empty string - Errors: {form.content.errors}')
        
        # Test whitespace-only content
        form_data = {
            'content': '   ',
            'csrf_token': 'test_token'
        }
        form = CommentForm(data=form_data)
        is_valid = form.validate()
        print(f'Whitespace - Valid: {is_valid}')
        print(f'Whitespace - Errors: {form.content.errors}')