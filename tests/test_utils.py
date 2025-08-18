"""
Unit tests for utility functions.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app.utils import log_admin_action, get_admin_actions
from app.models import AdminAction, User
from app import db


class TestLogAdminAction:
    """Test cases for log_admin_action utility function."""
    
    def test_log_admin_action_basic(self, db_session, test_admin):
        """Test basic admin action logging."""
        with patch('app.utils.current_user', test_admin):
            log_admin_action(
                action_type='create_user',
                target_type='user',
                target_id=1,
                description='Created test user'
            )
            
            # Check that action was logged
            action = AdminAction.query.first()
            assert action is not None
            assert action.admin_user_id == test_admin.id
            assert action.action_type == 'create_user'
            assert action.target_type == 'user'
            assert action.target_id == 1
            assert action.description == 'Created test user'
    
    def test_log_admin_action_with_target_user(self, db_session, test_admin, test_user):
        """Test admin action logging with target user."""
        with patch('app.utils.current_user', test_admin):
            log_admin_action(
                action_type='block_user',
                target_type='user',
                target_id=test_user.id,
                description=f'Blocked user {test_user.username}',
                target_user_id=test_user.id
            )
            
            action = AdminAction.query.first()
            assert action.target_user_id == test_user.id
            assert action.target_user == test_user
    
    def test_log_admin_action_with_dict_details(self, db_session, test_admin):
        """Test admin action logging with dictionary details."""
        details_dict = {
            'original_value': 'old',
            'new_value': 'new',
            'timestamp': '2023-01-01T00:00:00'
        }
        
        with patch('app.utils.current_user', test_admin):
            log_admin_action(
                action_type='edit_comment',
                target_type='comment',
                target_id=1,
                description='Edited comment',
                details=details_dict
            )
            
            action = AdminAction.query.first()
            assert action.details == json.dumps(details_dict)
    
    def test_log_admin_action_with_string_details(self, db_session, test_admin):
        """Test admin action logging with string details."""
        details_string = 'Additional details about the action'
        
        with patch('app.utils.current_user', test_admin):
            log_admin_action(
                action_type='delete_availability',
                target_type='availability',
                target_id=1,
                description='Deleted availability',
                details=details_string
            )
            
            action = AdminAction.query.first()
            assert action.details == details_string
    
    def test_log_admin_action_not_authenticated(self, db_session):
        """Test that action is not logged if user is not authenticated."""
        mock_user = MagicMock()
        mock_user.is_authenticated = False
        
        with patch('app.utils.current_user', mock_user):
            log_admin_action(
                action_type='create_user',
                target_type='user',
                target_id=1,
                description='Should not be logged'
            )
            
            # No action should be logged
            assert AdminAction.query.count() == 0
    
    def test_log_admin_action_not_admin(self, db_session, test_user):
        """Test that action is not logged if user is not admin."""
        with patch('app.utils.current_user', test_user):
            log_admin_action(
                action_type='create_user',
                target_type='user',
                target_id=1,
                description='Should not be logged'
            )
            
            # No action should be logged
            assert AdminAction.query.count() == 0
    
    def test_log_admin_action_database_error(self, db_session, test_admin):
        """Test handling of database errors during logging."""
        with patch('app.utils.current_user', test_admin):
            # Mock the db import inside the function
            with patch('app.utils.db') as mock_db:
                mock_db.session.commit.side_effect = Exception('Database error')
                with patch('app.utils.current_app') as mock_app:
                    mock_logger = MagicMock()
                    mock_app.logger = mock_logger
                    
                    log_admin_action(
                        action_type='create_user',
                        target_type='user',
                        target_id=1,
                        description='Test action'
                    )
                    
                    # Should handle error gracefully
                    mock_db.session.rollback.assert_called_once()
                    mock_logger.error.assert_called_once()
                    assert 'Failed to log admin action' in str(mock_logger.error.call_args)


class TestGetAdminActions:
    """Test cases for get_admin_actions utility function."""
    
    def test_get_admin_actions_basic(self, db_session, test_admin, test_factory):
        """Test basic retrieval of admin actions."""
        # Create test actions
        actions = []
        for i in range(3):
            action = test_factory.create_admin_action(
                admin_user=test_admin,
                action_type='create_user',
                description=f'Action {i+1}'
            )
            actions.append(action)
        
        retrieved_actions = get_admin_actions()
        
        assert len(retrieved_actions) == 3
        # Should be ordered by creation date descending
        assert retrieved_actions[0].description == 'Action 3'
        assert retrieved_actions[1].description == 'Action 2'
        assert retrieved_actions[2].description == 'Action 1'
    
    def test_get_admin_actions_with_limit(self, db_session, test_admin, test_factory):
        """Test retrieval with limit parameter."""
        # Create 5 test actions
        for i in range(5):
            test_factory.create_admin_action(
                admin_user=test_admin,
                description=f'Action {i+1}'
            )
        
        retrieved_actions = get_admin_actions(limit=3)
        
        assert len(retrieved_actions) == 3
        # Should get the 3 most recent
        assert retrieved_actions[0].description == 'Action 5'
        assert retrieved_actions[1].description == 'Action 4'
        assert retrieved_actions[2].description == 'Action 3'
    
    def test_get_admin_actions_filter_by_action_type(self, db_session, test_admin, test_factory):
        """Test filtering by action type."""
        # Create actions of different types
        test_factory.create_admin_action(
            admin_user=test_admin,
            action_type='create_user',
            description='Create action'
        )
        test_factory.create_admin_action(
            admin_user=test_admin,
            action_type='block_user',
            description='Block action'
        )
        test_factory.create_admin_action(
            admin_user=test_admin,
            action_type='create_user',
            description='Another create action'
        )
        
        retrieved_actions = get_admin_actions(action_type='create_user')
        
        assert len(retrieved_actions) == 2
        for action in retrieved_actions:
            assert action.action_type == 'create_user'
    
    def test_get_admin_actions_filter_by_target_type(self, db_session, test_admin, test_factory):
        """Test filtering by target type."""
        # Create actions with different target types
        test_factory.create_admin_action(
            admin_user=test_admin,
            target_type='user',
            description='User action'
        )
        test_factory.create_admin_action(
            admin_user=test_admin,
            target_type='comment',
            description='Comment action'
        )
        test_factory.create_admin_action(
            admin_user=test_admin,
            target_type='user',
            description='Another user action'
        )
        
        retrieved_actions = get_admin_actions(target_type='user')
        
        assert len(retrieved_actions) == 2
        for action in retrieved_actions:
            assert action.target_type == 'user'
    
    def test_get_admin_actions_combined_filters(self, db_session, test_admin, test_factory):
        """Test combining multiple filters."""
        # Create various actions
        test_factory.create_admin_action(
            admin_user=test_admin,
            action_type='create_user',
            target_type='user',
            description='Match both filters'
        )
        test_factory.create_admin_action(
            admin_user=test_admin,
            action_type='create_user',
            target_type='comment',
            description='Match action type only'
        )
        test_factory.create_admin_action(
            admin_user=test_admin,
            action_type='block_user',
            target_type='user',
            description='Match target type only'
        )
        
        retrieved_actions = get_admin_actions(
            action_type='create_user',
            target_type='user'
        )
        
        assert len(retrieved_actions) == 1
        assert retrieved_actions[0].description == 'Match both filters'
    
    def test_get_admin_actions_empty_result(self, db_session):
        """Test retrieval when no actions exist."""
        retrieved_actions = get_admin_actions()
        assert len(retrieved_actions) == 0
    
    def test_get_admin_actions_no_matching_filters(self, db_session, test_admin, test_factory):
        """Test retrieval with filters that don't match any actions."""
        test_factory.create_admin_action(
            admin_user=test_admin,
            action_type='create_user',
            target_type='user'
        )
        
        retrieved_actions = get_admin_actions(
            action_type='nonexistent_action',
            target_type='user'
        )
        
        assert len(retrieved_actions) == 0
    
    def test_get_admin_actions_multiple_admins(self, db_session, test_factory):
        """Test retrieval with actions from multiple admins."""
        admin1 = test_factory.create_admin_user(username='admin1')
        admin2 = test_factory.create_admin_user(username='admin2')
        
        test_factory.create_admin_action(
            admin_user=admin1,
            description='Action by admin1'
        )
        test_factory.create_admin_action(
            admin_user=admin2,
            description='Action by admin2'
        )
        
        retrieved_actions = get_admin_actions()
        
        assert len(retrieved_actions) == 2
        # Should include actions from both admins
        descriptions = [action.description for action in retrieved_actions]
        assert 'Action by admin1' in descriptions
        assert 'Action by admin2' in descriptions