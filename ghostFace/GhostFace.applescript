-- GhostFace Launcher AppleScript
-- This script launches the GhostFace web server and opens the browser

on run
	-- Get the directory where this script is located
	set scriptPath to POSIX path of (path to me as text)
	set scriptDir to do shell script "dirname " & quoted form of scriptPath
	
	-- Change to the ghostFace directory
	do shell script "cd " & quoted form of scriptDir
	
	-- Display a notification that we're starting
	display notification "Starting GhostFace web server..." with title "GhostFace"
	
	-- Start the Python server in the background
	set serverCommand to "python3 launch.py > /dev/null 2>&1 &"
	do shell script serverCommand
	
	-- Wait a moment for the server to start
	delay 3
	
	-- Open the browser to the correct URL
	do shell script "open 'http://localhost:5001'"
	
	-- Display success notification
	display notification "GhostFace is ready! Browser should open automatically." with title "GhostFace"
	
	-- Keep the script running to maintain the server process
	repeat
		delay 10
	end repeat
end run
