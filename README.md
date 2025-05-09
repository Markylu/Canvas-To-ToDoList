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

1. Run the application
2. If this is your first time, enter your API keys in the setup window
3. The application will automatically:
   - Fetch your Canvas courses and assignments
   - Create necessary labels in Todoist
   - Add new assignments as tasks
   - Remove assignment labels from completed tasks
4. A status window will show the progress of the sync

## Contributing

Feel free to submit issues and enhancement requests! 