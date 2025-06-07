from doc_to_jira import (
    DocToJira, 
    JiraConnectionError, 
    JiraConfigurationError, 
    JiraIssueCreationError, 
    JiraValidationError
)
import json
import logging

# Configure logging for the main application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_jira_from_raw():
    """Main function to initialize DocToJira and perform Jira operations."""
    try:
        logger.info("Initializing DocToJira client for raw issue creation")
        jira = DocToJira()
        
        summary = "Resolve Dodo bug."
        description = "The Dodo in GTA Liberty City takes too much time to lift off."
        issuetype = "Bug"
        
        logger.info(f"Creating issue: {summary}")
        issue_key = jira.create_jira_issue(summary, description, issuetype)
        logger.info(f"Successfully created issue: {issue_key}")
        
        return issue_key
        
    except JiraConfigurationError as ce:
        logger.error(f"Configuration problem: {ce}")
        print(f"Configuration Error: {ce}")
        return None
    except JiraConnectionError as conn_e:
        logger.error(f"Connection problem: {conn_e}")
        print(f"Connection Error: {conn_e}")
        return None
    except JiraValidationError as ve:
        logger.error(f"Validation error: {ve}")
        print(f"Validation Error: {ve}")
        return None
    except JiraIssueCreationError as ice:
        logger.error(f"Issue creation failed: {ice}")
        print(f"Issue Creation Error: {ice}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"An unexpected error occurred: {e}")
        return None


def run_jira_from_json(json_file_path: str):
    """
    Reads user stories and creates issues on Jira.
    
    Args:
        json_file_path: The path to the JSON file containing user stories.
        
    Returns:
        dict: Summary of created issues and any failures
    """
    results = {
        'created_issues': [],
        'failed_issues': [],
        'skipped_issues': []
    }
    
    try:
        logger.info(f"Initializing DocToJira client for JSON processing: {json_file_path}")
        jira = DocToJira()
        
        # Test connection before processing
        if not jira.test_connection():
            logger.error("Failed to establish connection to Jira")
            print("Error: Could not connect to Jira. Please check your configuration.")
            return results
        
        # Get project info for validation
        project_info = jira.get_project_info()
        if project_info:
            logger.info(f"Working with project: {project_info['name']} ({project_info['key']})")
            print(f"Connected to project: {project_info['name']} ({project_info['key']})")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            user_stories = json.load(f)
            
        if not isinstance(user_stories, list):
            raise TypeError("JSON file should contain a list of user stories.")
            
        logger.info(f"Processing {len(user_stories)} user stories from '{json_file_path}'")
        print(f"\nCreating Jira Issues from '{json_file_path}' ({len(user_stories)} stories)")

        for i, entry in enumerate(user_stories, 1):
            try:
                summary = entry.get("user_story", "").strip()
                description = entry.get("deliverables", "").strip()
                issuetype = entry.get("issue_type", "Story").strip()  # Allow override from JSON
                
                # Enhanced validation
                if not summary:
                    logger.warning(f"Skipping entry {i}: missing or empty 'user_story'")
                    results['skipped_issues'].append({
                        'entry': i,
                        'reason': "Missing or empty 'user_story'"
                    })
                    print(f"⚠️  Skipping story {i}: missing user_story")
                    continue
                    
                if not description:
                    logger.warning(f"Skipping entry {i}: missing or empty 'deliverables'")
                    results['skipped_issues'].append({
                        'entry': i,
                        'reason': "Missing or empty 'deliverables'"
                    })
                    print(f"⚠️  Skipping story {i}: missing deliverables")
                    continue
                
                logger.info(f"Processing story {i}: '{summary[:50]}...'")
                print(f"\n📝 Processing story {i}: '{summary}'")
                
                issue_key = jira.create_jira_issue(
                    summary=summary, 
                    description=description, 
                    issuetype=issuetype
                )
                
                results['created_issues'].append({
                    'entry': i,
                    'issue_key': issue_key,
                    'summary': summary
                })
                
                print(f"✅ Created issue: {issue_key}")
                logger.info(f"Successfully created issue {issue_key} for story {i}")
                
            except JiraValidationError as ve:
                error_msg = f"Validation failed for story {i}: {ve}"
                logger.error(error_msg)
                results['failed_issues'].append({
                    'entry': i,
                    'error': str(ve),
                    'summary': entry.get("user_story", "Unknown")
                })
                print(f"❌ Story {i} failed validation: {ve}")
                
            except JiraIssueCreationError as ice:
                error_msg = f"Failed to create issue for story {i}: {ice}"
                logger.error(error_msg)
                results['failed_issues'].append({
                    'entry': i,
                    'error': str(ice),
                    'summary': entry.get("user_story", "Unknown")
                })
                print(f"❌ Failed to create issue for story {i}: {ice}")
                
            except Exception as e:
                error_msg = f"Unexpected error processing story {i}: {e}"
                logger.error(error_msg)
                results['failed_issues'].append({
                    'entry': i,
                    'error': str(e),
                    'summary': entry.get("user_story", "Unknown")
                })
                print(f"❌ Unexpected error for story {i}: {e}")

        # Print summary
        print(f"\n📊 Processing Summary:")
        print(f"   ✅ Created: {len(results['created_issues'])} issues")
        print(f"   ❌ Failed: {len(results['failed_issues'])} issues")
        print(f"   ⚠️  Skipped: {len(results['skipped_issues'])} issues")
        
        if results['created_issues']:
            print(f"\n🎉 Successfully created issues:")
            for item in results['created_issues']:
                print(f"   • {item['issue_key']}: {item['summary'][:60]}...")
        
        if results['failed_issues']:
            print(f"\n⚠️  Failed issues (check logs for details):")
            for item in results['failed_issues']:
                print(f"   • Story {item['entry']}: {item['summary'][:50]}...")
        
        logger.info(f"JSON processing completed. Created: {len(results['created_issues'])}, "
                   f"Failed: {len(results['failed_issues'])}, Skipped: {len(results['skipped_issues'])}")

    except FileNotFoundError:
        error_msg = f"JSON file not found at {json_file_path}"
        logger.error(error_msg)
        print(f"❌ Error: {error_msg}")
    except json.JSONDecodeError as jde:
        error_msg = f"Could not decode JSON from {json_file_path}: {jde}"
        logger.error(error_msg)
        print(f"❌ JSON Error: {error_msg}")
    except TypeError as te:
        error_msg = f"JSON structure error: {te}"
        logger.error(error_msg)
        print(f"❌ Structure Error: {error_msg}")
    except JiraConfigurationError as ce:
        logger.error(f"Configuration problem: {ce}")
        print(f"❌ Configuration Error: {ce}")
    except JiraConnectionError as conn_e:
        logger.error(f"Connection problem: {conn_e}")
        print(f"❌ Connection Error: {conn_e}")
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg)
        print(f"❌ Unexpected error: {error_msg}")
    
    return results


def validate_json_structure(json_file_path: str) -> bool:
    """
    Validate the structure of the JSON file before processing.
    
    Args:
        json_file_path: Path to the JSON file
        
    Returns:
        bool: True if structure is valid, False otherwise
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("❌ JSON file should contain a list of user stories")
            return False
        
        required_fields = ['user_story', 'deliverables']
        valid_entries = 0
        
        for i, entry in enumerate(data, 1):
            if not isinstance(entry, dict):
                print(f"❌ Entry {i} should be a dictionary")
                continue
                
            missing_fields = [field for field in required_fields if not entry.get(field, "").strip()]
            if missing_fields:
                print(f"⚠️  Entry {i} missing required fields: {missing_fields}")
            else:
                valid_entries += 1
        
        print(f"📊 Validation Summary: {valid_entries}/{len(data)} entries are valid")
        return valid_entries > 0
        
    except FileNotFoundError:
        print(f"❌ File not found: {json_file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Jira Issue Creator")
    print("=" * 50)
    
    # Uncomment to test raw issue creation
    # print("\n1️⃣  Testing raw issue creation...")
    # run_jira_from_raw()
    
    # JSON file processing
    user_story_json = "user_stories.json"
    
    print(f"\n2️⃣  Validating JSON structure...")
    if validate_json_structure(user_story_json):
        print(f"\n3️⃣  Processing user stories from JSON...")
        results = run_jira_from_json(user_story_json)
        
        # Optional: Save results to file for audit trail
        if results['created_issues'] or results['failed_issues']:
            results_file = f"jira_creation_results_{json.loads('{}')}.json".replace('{}', 
                str(hash(user_story_json))[:8])
            try:
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"\n📄 Results saved to: {results_file}")
            except Exception as e:
                logger.warning(f"Could not save results file: {e}")
    else:
        print("❌ JSON validation failed. Please fix the file structure before proceeding.")