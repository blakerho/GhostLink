-- GhostFace Launcher AppleScript
-- This script launches the GhostFace web server and opens the browser

on run
	-- Get the directory where this script is located
	set scriptPath to POSIX path of (path to me as text)
	set scriptDir to do shell script "dirname " & quoted form of scriptPath
	
	-- Display a notification that we're starting
	display notification "Starting GhostFace..." with title "GhostFace"
	
	-- Use the robust launcher script
	set launcherCommand to "cd " & quoted form of scriptDir & " && ./robust_launcher.sh"
	do shell script launcherCommand
	
	-- Display success notification
	display notification "GhostFace launcher completed!" with title "GhostFace"
end run
