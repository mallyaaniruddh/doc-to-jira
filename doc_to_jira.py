# doc_to_jira.py

import os
import time
import logging
from jira import JIRA
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JiraConnectionError(Exception):
    """Raised when connection to Jira fails."""
    pass


class JiraConfigurationError(Exception):
    """Raised when Jira configuration is invalid or incomplete."""
    pass


class JiraIssueCreationError(Exception):
    """Raised when Jira issue creation fails."""
    pass


class JiraValidationError(Exception):
    """Raised when input validation fails."""
    pass


class DocToJira:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the DocToJira client with retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts for network operations
            retry_delay: Initial delay between retries in seconds (exponential backoff)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.info("Initializing DocToJira client")
        
        # Load and validate environment variables
        self.jira_base_url = os.getenv("JIRA_BASE_URL")
        self.jira_email = os.getenv("JIRA_EMAIL")
        self.jira_api_token = os.getenv("JIRA_API_TOKEN")
        self.jira_project_key = os.getenv("JIRA_PROJECT_KEY")

        self._validate_configuration()
        self.jira_client = self._connect_to_jira()
        
        logger.info("DocToJira client initialized successfully")

    def _validate_configuration(self) -> None:
        """Validate that all required environment variables are present."""
        missing_vars = []
        
        if not self.jira_base_url:
            missing_vars.append("JIRA_BASE_URL")
        if not self.jira_email:
            missing_vars.append("JIRA_EMAIL")
        if not self.jira_api_token:
            missing_vars.append("JIRA_API_TOKEN")
        if not self.jira_project_key:
            missing_vars.append("JIRA_PROJECT_KEY")
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}. " \
                       "Please ensure all Jira credentials are configured."
            logger.error(error_msg)
            raise JiraConfigurationError(error_msg)

    def _connect_to_jira(self) -> JIRA:
        """
        Connect to Jira with retry mechanism.
        
        Returns:
            JIRA: Connected Jira client instance
            
        Raises:
            JiraConnectionError: If connection fails after all retries
        """
        options = {'server': self.jira_base_url}
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Attempting to connect to Jira (attempt {attempt + 1}/{self.max_retries + 1})")
                
                jira = JIRA(
                    options=options,
                    basic_auth=(self.jira_email, self.jira_api_token)
                )
                
                logger.info("Successfully connected to Jira")
                return jira
                
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    error_msg = f"Failed to connect to Jira after {self.max_retries + 1} attempts: {e}"
                    logger.error(error_msg)
                    raise JiraConnectionError(error_msg) from e

    def _validate_issue_input(self, summary: str, description: str, issuetype: str) -> None:
        """
        Validate input parameters for issue creation.
        
        Args:
            summary: Issue summary/title
            description: Issue description
            issuetype: Issue type
            
        Raises:
            JiraValidationError: If any input is invalid
        """
        errors = []
        
        if not summary or not summary.strip():
            errors.append("Summary cannot be empty")
        elif len(summary.strip()) > 255:  # Jira summary limit
            errors.append("Summary cannot exceed 255 characters")
            
        if not description or not description.strip():
            errors.append("Description cannot be empty")
            
        if not issuetype or not issuetype.strip():
            errors.append("Issue type cannot be empty")
        
        if errors:
            error_msg = f"Input validation failed: {'; '.join(errors)}"
            logger.error(error_msg)
            raise JiraValidationError(error_msg)

    def create_jira_issue(self, summary: str, description: str, issuetype: str) -> str:
        """
        Create a Jira issue with retry mechanism.
        
        Args:
            summary: The main title of the issue
            description: Describes the issue in detail
            issuetype: Specifies the type of the issue (e.g., 'Bug', 'Task', 'Story')
        
        Returns:
            str: The issue key of the created issue
            
        Raises:
            JiraValidationError: If input validation fails
            JiraIssueCreationError: If issue creation fails after all retries
        """
        logger.info(f"Creating Jira issue with summary: '{summary[:50]}...'")
        
        # Validate input
        self._validate_issue_input(summary, description, issuetype)
        
        issue_fields = {
            'project': {'key': self.jira_project_key},
            'summary': summary.strip(),
            'description': description.strip(),
            'issuetype': {'name': issuetype.strip()}
        }

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Creating issue attempt {attempt + 1}/{self.max_retries + 1}")
                
                issue = self.jira_client.create_issue(fields=issue_fields)
                issue_key = issue.key
                
                logger.info(f"Successfully created Jira issue: {issue_key}")
                return issue_key
                
            except Exception as e:
                logger.warning(f"Issue creation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    error_msg = f"Failed to create Jira issue after {self.max_retries + 1} attempts: {e}"
                    logger.error(error_msg)
                    raise JiraIssueCreationError(error_msg) from e

    def test_connection(self) -> bool:
        """
        Test the connection to Jira by attempting to fetch user info.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            logger.info("Testing Jira connection")
            user = self.jira_client.current_user()
            logger.info(f"Connection test successful. Current user: {user}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_project_info(self) -> Optional[dict]:
        """
        Get information about the configured project.
        
        Returns:
            dict: Project information or None if project not found
        """
        try:
            logger.info(f"Fetching project info for: {self.jira_project_key}")
            project = self.jira_client.project(self.jira_project_key)
            
            project_info = {
                'key': project.key,
                'name': project.name,
                'description': getattr(project, 'description', 'No description'),
                'lead': project.lead.displayName if project.lead else 'No lead assigned'
            }
            
            logger.info(f"Successfully retrieved project info for: {project.name}")
            return project_info
            
        except Exception as e:
            logger.error(f"Failed to fetch project info: {e}")
            return None


# Example usage
if __name__ == "__main__":
    try:
        # Initialize the client with custom retry settings
        jira_client = DocToJira(max_retries=2, retry_delay=1.5)
        
        # Test connection
        if jira_client.test_connection():
            # Get project info
            project_info = jira_client.get_project_info()
            if project_info:
                logger.info(f"Working with project: {project_info['name']}")
            
            # Create a sample issue
            issue_key = jira_client.create_jira_issue(
                summary="Sample Issue from Enhanced Client",
                description="This is a test issue created by the enhanced DocToJira client with proper logging and error handling.",
                issuetype="Task"
            )
            
            logger.info(f"Demo completed successfully. Created issue: {issue_key}")
        else:
            logger.error("Connection test failed. Please check your configuration.")
            
    except (JiraConfigurationError, JiraConnectionError, JiraValidationError, JiraIssueCreationError) as e:
        logger.error(f"Application error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")