# Canvas to Todoist Sync

A desktop application that syncs your Canvas assignments to Todoist tasks.

## Features

- Automatically syncs Canvas assignments to Todoist
- Creates labels for courses and assignments
- Handles timezone conversion (UTC to EDT/EST)
- Removes assignment labels from completed tasks
- User-friendly GUI for setup and status updates
- Prevents duplicate tasks


## First Run Setup

On first run, you'll need to provide:
1. Canvas API URL (default: https://sps.instructure.com/)
2. Canvas API Key
3. Canvas User ID
4. Todoist API Key

### Getting API Keys

#### Canvas API Key
1. Log in to Canvas
2. Go to Account > Settings
3. Scroll down to "Approved Integrations"
4. Click "New Access Token"
5. Give it a name and copy the token

#### Canvas User ID
1. Log in to Canvas
2. Go to any course with a people tab
3. Find your name and click it
4. Your user ID is in the URL: https://sps.instructure.com/courses/COURSE_ID/users/**USER_ID**
5. Copy the number after /users/

#### Todoist API Key
1. Log in to Todoist
2. Go to Settings > Integrations
3. Go to Developer Tab
4. Copy your API token

## Usage

1. **First Run Setup**:
   - Run the application
   - Enter your Canvas API URL (e.g., https://sps.instructure.com/)
   - Enter your Canvas API Key
   - Enter your Canvas User ID
   - Enter your Todoist API Key
   - Click "Save Configuration"

2. **Regular Usage**:
   - Run the application
   - The sync process will start automatically
   - Tasks will be created in Todoist with:
     - Assignment name as the task title
     - Assignment URL in the description
     - Due date in your local timezone
     - Course name as a label

3. **Task Management**:
   - Tasks are automatically labeled with their course names
   - Completed tasks are tracked
   - Duplicate tasks are prevented using a cache system
   - Tasks with expired due dates are automatically removed from the cache

4. **Cache Management**:
   - The application maintains a cache of tasks to prevent duplicates
   - Cache is automatically cleaned up for expired tasks
   - You can manually clear the cache using:
     - Press Ctrl+Option+Command+Shift+Delete (⌃⌥⌘⇧⌫)
     - Or click the "Clear Cache" button
   - Cache is stored in `task_cache.json` in the application directory

5. **Troubleshooting**:
   - If tasks are duplicated, try clearing the cache
   - If the sync fails, check your API keys and internet connection
   - The application will show detailed status messages during the sync process

## Contributing

Feel free to submit issues and enhancement requests! 