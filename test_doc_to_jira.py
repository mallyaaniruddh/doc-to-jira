# test_doc_to_jira.py

import unittest
import os
import logging
from unittest.mock import Mock, patch, MagicMock, call
from doc_to_jira import (
    DocToJira, 
    JiraConnectionError, 
    JiraConfigurationError, 
    JiraIssueCreationError, 
    JiraValidationError
)

# Disable logging during tests to reduce noise
logging.disable(logging.CRITICAL)


class TestDocToJiraConfiguration(unittest.TestCase):
    """Test configuration and initialization."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.valid_env_vars = {
            'JIRA_BASE_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token-123',
            'JIRA_PROJECT_KEY': 'TEST'
        }
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_missing_all_credentials_raises_configuration_error(self):
        """Test that missing all credentials raise JiraConfigurationError."""
        with self.assertRaises(JiraConfigurationError) as context:
            DocToJira()
        
        error_msg = str(context.exception)
        self.assertIn("Missing required environment variables", error_msg)
        self.assertIn("JIRA_BASE_URL", error_msg)
        self.assertIn("JIRA_EMAIL", error_msg)
        self.assertIn("JIRA_API_TOKEN", error_msg)
        self.assertIn("JIRA_PROJECT_KEY", error_msg)
    
    @patch.dict(os.environ, {
        'JIRA_BASE_URL': 'https://test.atlassian.net',
        'JIRA_EMAIL': 'test@example.com',
        # Missing JIRA_API_TOKEN and JIRA_PROJECT_KEY
    }, clear=True)
    def test_init_partial_credentials_raises_configuration_error(self):
        """Test that partial credentials raise JiraConfigurationError."""
        with self.assertRaises(JiraConfigurationError) as context:
            DocToJira()
        
        error_msg = str(context.exception)
        self.assertIn("Missing required environment variables", error_msg)
        self.assertIn("JIRA_API_TOKEN", error_msg)
        self.assertIn("JIRA_PROJECT_KEY", error_msg)
        self.assertNotIn("JIRA_BASE_URL", error_msg)
        self.assertNotIn("JIRA_EMAIL", error_msg)
    
    @patch('doc_to_jira.JIRA')
    @patch.dict(os.environ, {
        'JIRA_BASE_URL': 'https://test.atlassian.net',
        'JIRA_EMAIL': 'test@example.com',
        'JIRA_API_TOKEN': 'test-token-123',
        'JIRA_PROJECT_KEY': 'TEST'
    }, clear=True)
    def test_init_with_valid_credentials_and_custom_retry_settings(self, mock_jira):
        """Test successful initialization with valid credentials and custom retry settings."""
        mock_jira_instance = Mock()
        mock_jira.return_value = mock_jira_instance
        
        doc_to_jira = DocToJira(max_retries=5, retry_delay=2.0)
        
        self.assertEqual(doc_to_jira.jira_base_url, 'https://test.atlassian.net')
        self.assertEqual(doc_to_jira.jira_email, 'test@example.com')
        self.assertEqual(doc_to_jira.jira_api_token, 'test-token-123')
        self.assertEqual(doc_to_jira.jira_project_key, 'TEST')
        self.assertEqual(doc_to_jira.max_retries, 5)
        self.assertEqual(doc_to_jira.retry_delay, 2.0)
        self.assertEqual(doc_to_jira.jira_client, mock_jira_instance)


class TestDocToJiraConnection(unittest.TestCase):
    """Test connection handling and retry mechanisms."""
    
    @patch('doc_to_jira.JIRA')
    @patch('doc_to_jira.time.sleep')  # Mock sleep to speed up tests
    @patch.dict(os.environ, {
        'JIRA_BASE_URL': 'https://test.atlassian.net',
        'JIRA_EMAIL': 'test@example.com',
        'JIRA_API_TOKEN': 'test-token-123',
        'JIRA_PROJECT_KEY': 'TEST'
    }, clear=True)
    def test_connection_success_on_first_attempt(self, mock_sleep, mock_jira):
        """Test successful connection on first attempt."""
        mock_jira_instance = Mock()
        mock_jira.return_value = mock_jira_instance
        
        doc_to_jira = DocToJira(max_retries=3, retry_delay=1.0)
        
        # Should not have slept since connection succeeded on first try
        mock_sleep.assert_not_called()
        mock_jira.assert_called_once_with(
            options={'server': 'https://test.atlassian.net'},
            basic_auth=('test@example.com', 'test-token-123')
        )
    
    @patch('doc_to_jira.JIRA')
    @patch('doc_to_jira.time.sleep')
    @patch.dict(os.environ, {
        'JIRA_BASE_URL': 'https://test.atlassian.net',
        'JIRA_EMAIL': 'test@example.com',
        'JIRA_API_TOKEN': 'test-token-123',
        'JIRA_PROJECT_KEY': 'TEST'
    }, clear=True)
    def test_connection_success_after_retries(self, mock_sleep, mock_jira):
        """Test successful connection after retries."""
        # First two calls fail, third succeeds
        mock_jira_instance = Mock()
        mock_jira.side_effect = [
            Exception("Connection failed"),
            Exception("Connection failed"),
            mock_jira_instance
        ]
        
        doc_to_jira = DocToJira(max_retries=3, retry_delay=1.0)
        
        # Should have made 3 attempts total
        self.assertEqual(mock_jira.call_count, 3)
        
        # Should have slept twice (after first and second failures)
        expected_calls = [call(1.0), call(2.0)]  # Exponential backoff: 1.0, 2.0
        mock_sleep.assert_has_calls(expected_calls)
        
        self.assertEqual(doc_to_jira.jira_client, mock_jira_instance)
    
    @patch('doc_to_jira.JIRA')
    @patch('doc_to_jira.time.sleep')
    @patch.dict(os.environ, {
        'JIRA_BASE_URL': 'https://test.atlassian.net',
        'JIRA_EMAIL': 'test@example.com',
        'JIRA_API_TOKEN': 'test-token-123',
        'JIRA_PROJECT_KEY': 'TEST'
    }, clear=True)
    def test_connection_failure_after_all_retries(self, mock_sleep, mock_jira):
        """Test connection failure after all retries exhausted."""
        mock_jira.side_effect = Exception("Connection failed")
        
        with self.assertRaises(JiraConnectionError) as context:
            DocToJira(max_retries=2, retry_delay=0.5)
        
        # Should have made 3 attempts total (initial + 2 retries)
        self.assertEqual(mock_jira.call_count, 3)
        
        # Should have slept twice
        expected_calls = [call(0.5), call(1.0)]  # Exponential backoff
        mock_sleep.assert_has_calls(expected_calls)
        
        error_msg = str(context.exception)
        self.assertIn("Failed to connect to Jira after 3 attempts", error_msg)
        self.assertIn("Connection failed", error_msg)


class TestDocToJiraIssueCreation(unittest.TestCase):
    """Test issue creation with validation and retry mechanisms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch.dict(os.environ, {
            'JIRA_BASE_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token-123',
            'JIRA_PROJECT_KEY': 'TEST'
        }, clear=True)
        self.patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.patcher.stop()
    
    def test_create_issue_input_validation_empty_summary(self):
        """Test input validation for empty summary."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira.return_value = Mock()
            doc_to_jira = DocToJira()
            
            with self.assertRaises(JiraValidationError) as context:
                doc_to_jira.create_jira_issue("", "Valid description", "Bug")
            
            self.assertIn("Summary cannot be empty", str(context.exception))
    
    def test_create_issue_input_validation_empty_description(self):
        """Test input validation for empty description."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira.return_value = Mock()
            doc_to_jira = DocToJira()
            
            with self.assertRaises(JiraValidationError) as context:
                doc_to_jira.create_jira_issue("Valid summary", "", "Bug")
            
            self.assertIn("Description cannot be empty", str(context.exception))
    
    def test_create_issue_input_validation_empty_issuetype(self):
        """Test input validation for empty issue type."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira.return_value = Mock()
            doc_to_jira = DocToJira()
            
            with self.assertRaises(JiraValidationError) as context:
                doc_to_jira.create_jira_issue("Valid summary", "Valid description", "")
            
            self.assertIn("Issue type cannot be empty", str(context.exception))
    
    def test_create_issue_input_validation_summary_too_long(self):
        """Test input validation for summary exceeding character limit."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira.return_value = Mock()
            doc_to_jira = DocToJira()
            
            long_summary = "x" * 256  # Exceeds 255 character limit
            
            with self.assertRaises(JiraValidationError) as context:
                doc_to_jira.create_jira_issue(long_summary, "Valid description", "Bug")
            
            self.assertIn("Summary cannot exceed 255 characters", str(context.exception))
    
    def test_create_issue_input_validation_multiple_errors(self):
        """Test input validation with multiple errors."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira.return_value = Mock()
            doc_to_jira = DocToJira()
            
            with self.assertRaises(JiraValidationError) as context:
                doc_to_jira.create_jira_issue("", "", "")
            
            error_msg = str(context.exception)
            self.assertIn("Summary cannot be empty", error_msg)
            self.assertIn("Description cannot be empty", error_msg)
            self.assertIn("Issue type cannot be empty", error_msg)
    
    @patch('doc_to_jira.time.sleep')
    def test_create_issue_success_on_first_attempt(self, mock_sleep):
        """Test successful issue creation on first attempt."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira_instance = Mock()
            mock_issue = Mock()
            mock_issue.key = 'TEST-123'
            mock_jira_instance.create_issue.return_value = mock_issue
            mock_jira.return_value = mock_jira_instance
            
            doc_to_jira = DocToJira()
            result = doc_to_jira.create_jira_issue(
                summary="Test Issue",
                description="Test Description",
                issuetype="Bug"
            )
            
            self.assertEqual(result, 'TEST-123')
            mock_sleep.assert_not_called()
            
            expected_fields = {
                'project': {'key': 'TEST'},
                'summary': 'Test Issue',
                'description': 'Test Description',
                'issuetype': {'name': 'Bug'}
            }
            mock_jira_instance.create_issue.assert_called_once_with(fields=expected_fields)
    
    @patch('doc_to_jira.time.sleep')
    def test_create_issue_success_after_retries(self, mock_sleep):
        """Test successful issue creation after retries."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira_instance = Mock()
            mock_issue = Mock()
            mock_issue.key = 'TEST-456'
            
            # First two calls fail, third succeeds
            mock_jira_instance.create_issue.side_effect = [
                Exception("Network error"),
                Exception("Server error"),
                mock_issue
            ]
            mock_jira.return_value = mock_jira_instance
            
            doc_to_jira = DocToJira(max_retries=3, retry_delay=0.5)
            result = doc_to_jira.create_jira_issue(
                summary="Test Issue",
                description="Test Description",
                issuetype="Bug"
            )
            
            self.assertEqual(result, 'TEST-456')
            self.assertEqual(mock_jira_instance.create_issue.call_count, 3)
            
            # Should have slept twice (after first and second failures)
            expected_calls = [call(0.5), call(1.0)]  # Exponential backoff
            mock_sleep.assert_has_calls(expected_calls)
    
    @patch('doc_to_jira.time.sleep')
    def test_create_issue_failure_after_all_retries(self, mock_sleep):
        """Test issue creation failure after all retries exhausted."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira_instance = Mock()
            mock_jira_instance.create_issue.side_effect = Exception("Persistent error")
            mock_jira.return_value = mock_jira_instance
            
            doc_to_jira = DocToJira(max_retries=2, retry_delay=0.2)
            
            with self.assertRaises(JiraIssueCreationError) as context:
                doc_to_jira.create_jira_issue(
                    summary="Test Issue",
                    description="Test Description",
                    issuetype="Bug"
                )
            
            # Should have made 3 attempts total
            self.assertEqual(mock_jira_instance.create_issue.call_count, 3)
            
            # Should have slept twice
            expected_calls = [call(0.2), call(0.4)]  # Exponential backoff
            mock_sleep.assert_has_calls(expected_calls)
            
            error_msg = str(context.exception)
            self.assertIn("Failed to create Jira issue after 3 attempts", error_msg)
            self.assertIn("Persistent error", error_msg)


class TestDocToJiraUtilityMethods(unittest.TestCase):
    """Test utility methods like test_connection and get_project_info."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch.dict(os.environ, {
            'JIRA_BASE_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token-123',
            'JIRA_PROJECT_KEY': 'TEST'
        }, clear=True)
        self.patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.patcher.stop()
    
    def test_connection_test_success(self):
        """Test successful connection test."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira_instance = Mock()
            mock_jira_instance.current_user.return_value = "test_user"
            mock_jira.return_value = mock_jira_instance
            
            doc_to_jira = DocToJira()
            result = doc_to_jira.test_connection()
            
            self.assertTrue(result)
            mock_jira_instance.current_user.assert_called_once()
    
    def test_connection_test_failure(self):
        """Test connection test failure."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira_instance = Mock()
            mock_jira_instance.current_user.side_effect = Exception("Auth failed")
            mock_jira.return_value = mock_jira_instance
            
            doc_to_jira = DocToJira()
            result = doc_to_jira.test_connection()
            
            self.assertFalse(result)
    
    def test_get_project_info_success(self):
        """Test successful project info retrieval."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira_instance = Mock()
            mock_project = Mock()
            mock_project.key = 'TEST'
            mock_project.name = 'Test Project'
            mock_project.description = 'A test project'
            mock_project.lead.displayName = 'John Doe'
            mock_jira_instance.project.return_value = mock_project
            mock_jira.return_value = mock_jira_instance
            
            doc_to_jira = DocToJira()
            result = doc_to_jira.get_project_info()
            
            expected_info = {
                'key': 'TEST',
                'name': 'Test Project',
                'description': 'A test project',
                'lead': 'John Doe'
            }
            
            self.assertEqual(result, expected_info)
            mock_jira_instance.project.assert_called_once_with('TEST')
    
    def test_get_project_info_failure(self):
        """Test project info retrieval failure."""
        with patch('doc_to_jira.JIRA') as mock_jira:
            mock_jira_instance = Mock()
            mock_jira_instance.project.side_effect = Exception("Project not found")
            mock_jira.return_value = mock_jira_instance
            
            doc_to_jira = DocToJira()
            result = doc_to_jira.get_project_info()
            
            self.assertIsNone(result)


class TestDocToJiraIntegration(unittest.TestCase):
    """
    Integration tests that would run against a real JIRA instance.
    These are skipped but show what integration tests would look like.
    """
    
    @unittest.skip("Requires actual JIRA instance")
    def test_real_jira_connection_with_retry(self):
        """Test connection to real JIRA instance with retry mechanism."""
        # This would test against a real JIRA instance
        pass
    
    @unittest.skip("Requires actual JIRA instance")
    def test_real_issue_creation_with_validation(self):
        """Test creating real JIRA issue with enhanced validation."""
        # This would create and then clean up a real JIRA issue
        pass
    
    @unittest.skip("Requires actual JIRA instance")
    def test_real_retry_mechanism_under_network_issues(self):
        """Test retry mechanism under real network conditions."""
        # This would test retry behavior with actual network issues
        pass


if __name__ == '__main__':
    # Re-enable logging for manual test runs
    logging.disable(logging.NOTSET)
    
    # Run tests with verbose output
    unittest.main(verbosity=2)