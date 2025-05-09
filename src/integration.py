import datetime
import requests
from canvasapi import Canvas
from canvasapi.exceptions import Forbidden
from todoist_api_python.api import TodoistAPI
import concurrent.futures
from functools import lru_cache
import json
import os
import sys

def get_course_name(course):
    """Get the course name safely, with fallback options."""
    try:
        if hasattr(course, 'name'):
            return course.name
        elif hasattr(course, 'course_code'):
            return course.course_code
        else:
            return f"Course {course.id}"
    except Exception:
        return f"Unknown Course {course.id if hasattr(course, 'id') else 'ID Unknown'}"

def get_cache_path():
    """Get the path to the task cache file."""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle
        application_path = os.path.dirname(sys.executable)
    else:
        # If the application is run from a Python interpreter
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    cache_path = os.path.join(application_path, 'task_cache.json')
    return cache_path

class CanvasTodoistSync:
    def __init__(self, canvas_api_url, canvas_api_key, todoist_api_key, user_id):
        """Initialize the sync with API credentials."""
        try:
            self.canvas = Canvas(canvas_api_url, canvas_api_key)
            self.todoist = TodoistAPI(todoist_api_key)
            self.user_id = int(user_id)
            self.existing_labels = {}
            self.existing_task_set = set()
            self.completed_tasks = []
            self.course_cache = {}
            self.cache_path = get_cache_path()
            
            # Verify connections
            self.user = self.canvas.get_user(self.user_id)
            if not self.user:
                raise Exception("Could not get user information from Canvas")
            if not self.todoist.get_projects():
                raise Exception("Could not connect to Todoist")
                
        except ValueError:
            raise Exception("Invalid user ID. Please ensure it's a valid number.")
        except Exception as e:
            raise Exception(f"Failed to initialize: {str(e)}")

    @lru_cache(maxsize=100)
    def get_cached_course(self, course_id):
        """Cache course data to reduce API calls."""
        return self.canvas.get_course(course_id)

    def load_task_cache(self):
        """Load the task cache from file."""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r') as f:
                    cache_data = json.load(f)
                    # Convert the cache data to a set of task IDs
                    current_time = datetime.datetime.now(datetime.timezone.utc)
                    valid_tasks = set()
                    
                    for task_id, due_date in cache_data.items():
                        # Skip tasks with expired due dates
                        if due_date:
                            try:
                                # Remove 'Z' and parse the date
                                clean_date = due_date.replace('Z', '')
                                task_due = datetime.datetime.fromisoformat(clean_date).replace(tzinfo=datetime.timezone.utc)
                                if task_due > current_time:
                                    valid_tasks.add(task_id)
                            except ValueError:
                                # If date parsing fails, keep the task
                                valid_tasks.add(task_id)
                        else:
                            # Keep tasks without due dates
                            valid_tasks.add(task_id)
                    
                    print(f"Loaded {len(valid_tasks)} tasks from cache")
                    return valid_tasks
            return set()
        except Exception as e:
            print(f"Error loading task cache: {str(e)}")
            return set()

    def save_task_cache(self):
        """Save the task cache to file."""
        try:
            # Convert the task set to a dictionary with due dates
            cache_data = {}
            tasks = list(self.todoist.get_tasks())  # Get all tasks once
            
            # First, add all tasks from Todoist
            for task in tasks:
                if not hasattr(task, 'content'):
                    continue
                    
                task_id = f"{task.content}|{task.description if hasattr(task, 'description') else ''}"
                if hasattr(task, 'due') and task.due:
                    cache_data[task_id] = task.due.date
                else:
                    cache_data[task_id] = None
            
            # Then, ensure all tasks in our set are included
            for task_id in self.existing_task_set:
                if task_id not in cache_data:
                    cache_data[task_id] = None
            
            print(f"Saving {len(cache_data)} tasks to cache")
            with open(self.cache_path, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Error saving task cache: {str(e)}")

    def fetch_existing_labels(self, update_status):
        """Fetch existing Todoist labels."""
        update_status("\nFetching existing Todoist labels...")
        try:
            labels = self.todoist.get_labels()
            # Handle both list and direct label objects
            self.existing_labels = {}
            for label in labels:
                if isinstance(label, list):
                    for l in label:
                        if hasattr(l, 'name') and hasattr(l, 'id'):
                            self.existing_labels[l.name] = l.id
                else:
                    if hasattr(label, 'name') and hasattr(label, 'id'):
                        self.existing_labels[label.name] = label.id
            
            update_status(f"Found {len(self.existing_labels)} existing labels")
            if self.existing_labels:
                update_status("Labels found: " + ", ".join(self.existing_labels.keys()))
        except Exception as e:
            update_status(f"Error fetching labels: {str(e)}")
            self.existing_labels = {}

    def fetch_existing_tasks(self, update_status):
        """Fetch existing Todoist tasks."""
        update_status("\nFetching existing Todoist tasks...")
        try:
            # Load cached tasks first
            self.existing_task_set = self.load_task_cache()
            update_status(f"Loaded {len(self.existing_task_set)} valid tasks from cache")
            
            # Fetch current tasks from Todoist
            existing_tasks = list(self.todoist.get_tasks())
            self.completed_tasks = []
            
            # Update cache with current tasks
            for task in existing_tasks:
                if isinstance(task, list):
                    continue
                    
                if hasattr(task, 'content'):
                    # Create a unique identifier for the task
                    task_id = f"{task.content}|{task.description if hasattr(task, 'description') else ''}"
                    self.existing_task_set.add(task_id)
                    
                    # Track completed tasks
                    if hasattr(task, 'completed_at') and task.completed_at is not None:
                        self.completed_tasks.append(task)
            
            # Save updated cache
            self.save_task_cache()
            
            update_status(f"Found {len(self.existing_task_set)} total unique tasks")
            update_status(f"Found {len(self.completed_tasks)} completed tasks")
            
            # Debug: Show some existing tasks
            if self.existing_task_set:
                update_status("\nSample of existing tasks:")
                for task_id in list(self.existing_task_set)[:5]:
                    content, desc = task_id.split('|', 1)
                    update_status(f"- {content}")
        except Exception as e:
            update_status(f"Error processing existing tasks: {str(e)}")
            self.existing_task_set = set()
            self.completed_tasks = []

    def process_course(self, course):
        """Process a single course and its assignments."""
        try:
            course_name = get_course_name(course)
            assignments = list(course.get_assignments())
            toadd = []
            
            for assignment in assignments:
                if assignment.due_at is None:
                    continue
                    
                due_at_datetime = datetime.datetime.fromisoformat(assignment.due_at[:-1])
                if due_at_datetime > datetime.datetime.now():
                    toadd.append((assignment, course))
                    
            return course_name, toadd
        except Forbidden:
            return get_course_name(course), []
        except Exception:
            return get_course_name(course), []

    def process_courses(self, update_status):
        """Process all courses and their assignments in parallel."""
        update_status("Getting user information...")
        user = self.canvas.get_user(self.user_id)
        update_status(f"Got user: {user.name}")

        update_status("Getting courses...")
        courses = list(user.get_courses())
        update_status(f"Found {len(courses)} courses")

        toadd = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_course = {executor.submit(self.process_course, course): course for course in courses}
            for future in concurrent.futures.as_completed(future_to_course):
                course = future_to_course[future]
                try:
                    course_name, course_toadd = future.result()
                    if course_toadd:
                        update_status(f"\nFound {len(course_toadd)} assignments in {course_name}")
                        toadd.extend(course_toadd)
                except Exception as e:
                    update_status(f"Error processing course {get_course_name(course)}: {str(e)}")

        return toadd

    def add_tasks(self, toadd, update_status):
        """Add new tasks to Todoist in batches."""
        if not toadd:
            update_status("\nNo new assignments to add.")
            return

        update_status("\nProcessing new assignments...")
        tasks_to_add = []
        labels_to_create = set()
        cache_updates = {}  # Store task IDs and their Canvas due dates

        # Prepare tasks and labels
        for assignment, course in toadd:
            task_content = f"Assignment: {assignment.name}"
            task_description = assignment.html_url
            
            # Create a unique identifier for the task
            task_id = f"{task_content}|{task_description}"
            
            # Check for duplicates
            if task_id in self.existing_task_set:
                update_status(f"Skipping duplicate task: {task_content}")
                continue

            course_name = get_course_name(course)

            # Only collect course labels
            if course_name not in self.existing_labels:
                labels_to_create.add(course_name)

            # Convert UTC to EDT/EST
            due_datetime = datetime.datetime.fromisoformat(assignment.due_at[:-1]).replace(tzinfo=datetime.timezone.utc)
            is_dst = datetime.datetime.now().astimezone().dst() != datetime.timedelta(0)
            eastern = datetime.timezone(datetime.timedelta(hours=-4 if is_dst else -5))
            due_datetime = due_datetime.astimezone(eastern)

            # Store the Canvas due date for caching (without 'Z')
            cache_updates[task_id] = assignment.due_at[:-1]

            # Only include course labels
            valid_labels = []
            if course_name in self.existing_labels:
                valid_labels.append(self.existing_labels[course_name])

            tasks_to_add.append({
                'content': task_content,
                'labels': valid_labels,  # Only include course labels
                'description': task_description,
                'due_datetime': due_datetime
            })

        # Create missing labels in parallel
        if labels_to_create:
            update_status(f"\nCreating {len(labels_to_create)} new course labels...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_label = {}
                for label_name in labels_to_create:
                    # Sanitize label name to remove invalid characters
                    sanitized_name = ''.join(c for c in label_name if c.isalnum() or c in ' -_')
                    if sanitized_name:  # Only create label if we have a valid name
                        future_to_label[executor.submit(self.todoist.add_label, name=sanitized_name)] = label_name

                for future in concurrent.futures.as_completed(future_to_label):
                    label_name = future_to_label[future]
                    try:
                        new_label = future.result()
                        self.existing_labels[label_name] = new_label.id
                        update_status(f"Created course label: {label_name}")
                    except Exception as e:
                        update_status(f"Error creating course label {label_name}: {str(e)}")

        # Add tasks in parallel
        if tasks_to_add:
            update_status(f"\nAdding {len(tasks_to_add)} new tasks...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for task in tasks_to_add:
                    # Create a copy of the task without None values
                    task_data = {k: v for k, v in task.items() if v is not None}
                    if task_data.get('labels'):  # Only include labels if we have valid ones
                        futures.append(executor.submit(self.todoist.add_task, **task_data))
                    else:
                        # If no valid labels, add task without labels
                        task_data.pop('labels', None)
                        futures.append(executor.submit(self.todoist.add_task, **task_data))

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        # Add to existing tasks set to prevent duplicates
                        task_id = f"{result.content}|{result.description if hasattr(result, 'description') else ''}"
                        self.existing_task_set.add(task_id)
                        update_status(f"Added task: {result.content}")
                    except Exception as e:
                        update_status(f"Error adding task: {str(e)}")
                        update_status(f"Task data: {task_data}")  # Log the task data for debugging

            # Update cache with new tasks and their Canvas due dates
            self.update_cache_with_canvas_dates(cache_updates)

    def update_cache_with_canvas_dates(self, new_dates):
        """Update the cache with Canvas due dates."""
        try:
            # Load existing cache
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r') as f:
                    cache_data = json.load(f)
            else:
                cache_data = {}

            # Update with new dates
            cache_data.update(new_dates)

            # Save updated cache
            with open(self.cache_path, 'w') as f:
                json.dump(cache_data, f)
            
            print(f"Updated cache with {len(new_dates)} new dates")
        except Exception as e:
            print(f"Error updating cache with Canvas dates: {str(e)}")

    def sync(self, update_status):
        """Perform the full sync process."""
        try:
            # Fetch existing data
            self.fetch_existing_labels(update_status)
            self.fetch_existing_tasks(update_status)
            
            # Clean up completed tasks
            self.cleanup_completed_tasks(update_status)
            
            # Process courses and get assignments to add
            toadd = self.process_courses(update_status)
            
            # Add new tasks
            self.add_tasks(toadd, update_status)
            
            update_status("\nSync completed successfully!")
            return True
        except Exception as e:
            update_status(f"\nError: {str(e)}")
            return False 