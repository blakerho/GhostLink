# GhostFace - GhostLink Web Interface

A modern web interface for the GhostLink audio encoder/decoder that makes it easy to encode text into audio files and decode them back. **Now with built-in installation!**

## Features

- **One-Click Installation**: Install GhostLink and dependencies directly from the web interface
- **Modern Dark Theme**: Clean, eye-friendly interface with soft colors
- **Real-time Command Preview**: See exactly what GhostLink commands will be executed
- **Multiple Input Modes**: Text, file, or directory encoding
- **Batch Processing**: Process multiple files at once
- **Live API Integration**: Actually executes GhostLink commands, not just a mockup
- **Drag & Drop Support**: Easy file and directory selection
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Option 1: Automatic Installation (Recommended)

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd GhostLink/ghostFace
   ```

2. **Start the Web Interface**
   ```bash
   # Option A: Use the launcher (recommended)
   python3 launch.py
   
   # Option B: Direct start
   python3 start_ghostlink_web.py
   ```

3. **Open in Browser**
   Open your browser and go to: **http://localhost:5001**

4. **Install Components**
   - Click the "Install" tab
   - Click "Check Status" to see what needs to be installed
   - Click "Install Everything" to install all required components
   - Wait for installation to complete

5. **Start Using**
   - Go to the "Encode" tab
   - Select the **parent GhostLink directory** (the folder containing the 'ghostlink' folder)
   - Start encoding and decoding!

### Option 2: Manual Installation

If you prefer to install manually:

```bash
# Install Flask and other web dependencies
pip install -r requirements_api.txt

# Install GhostLink package
cd ..
pip install -e .

# Start the web server
cd ghostFace
python start_ghostlink_web.py
```

## How to Use

### Encoding

1. **Select GhostLink Directory**: Choose your GhostLink installation directory
2. **Choose Input Method**:
   - **Text**: Type your message directly
   - **File**: Select a text file to encode
   - **Directory**: Select a folder with multiple text files
3. **Configure Audio Settings**:
   - FSK Mode (Dense/Sparse)
   - Mix Profile (Streaming/Studio)
   - Sample Rate, Baud Rate, Amplitude
   - Error correction settings
4. **Select Output Directory**: Choose where to save the encoded audio files
5. **Click "Encode Message"**: The system will process your input and create WAV files

### Decoding

1. **Select GhostLink Directory**: Same as encoding
2. **Choose Audio File**: Select a WAV/MP3/FLAC file to decode
3. **Configure Decoder Settings**: Match the settings used during encoding
4. **Click "Decode Message"**: The system will extract the hidden text

### Batch Processing

1. **Select Processing Mode**: Encode multiple files, decode multiple files, etc.
2. **Choose Input Directory**: Folder containing files to process
3. **Choose Output Directory**: Where to save results
4. **Click "Process Batch"**: Process all files automatically

## File Structure

```
GhostLink/
├── ghostFace/                 # Web interface folder
│   ├── GhostWeb.html          # Main web interface
│   ├── ghostlink_api.py       # Flask API backend
│   ├── start_ghostlink_web.py # Startup script
│   ├── launch.py              # Simple launcher script
│   ├── requirements_api.txt   # Python dependencies
│   └── README_Web_Interface.md # This file
├── ghostlink/                 # GhostLink Python package
│   ├── __main__.py            # Main encoder
│   ├── decoder.py             # Decoder
│   └── ...
└── ...
```

## Installation Features

The web interface includes a built-in installation system that makes setup easy:

### Installation Tab Features

- **Status Check**: Automatically detects what's installed and what's missing
- **Individual Installation**: Install GhostLink or web dependencies separately
- **One-Click Install**: Install everything with a single button
- **Real-time Feedback**: See installation progress and results
- **Error Handling**: Clear error messages if installation fails

### What Gets Installed

- **GhostLink Package**: The main audio encoding/decoding functionality
- **Web Dependencies**: Flask, Flask-CORS, and other web server components
- **Module Verification**: Ensures all required modules are available

## API Endpoints

The web interface communicates with the backend via these API endpoints:

- `GET /api/install/check` - Check installation status
- `POST /api/install/dependencies` - Install web dependencies
- `POST /api/install/ghostlink` - Install GhostLink package
- `POST /api/install/all` - Install all components
- `POST /api/encode` - Encode text, file, or directory
- `POST /api/decode` - Decode audio file
- `POST /api/batch` - Batch processing
- `GET /api/health` - Health check

## Troubleshooting

### Common Issues

1. **"Installation failed"**
   - Make sure you have pip installed and accessible
   - Check that you have write permissions to install packages
   - Try running the terminal with elevated permissions if needed
   - Check the installation log for specific error messages

2. **"GhostLink directory not found"**
   - Make sure you've selected the correct GhostLink directory
   - The directory should contain the `ghostlink` Python package
   - Try using the installation tab to install GhostLink first

3. **"Permission denied"**
   - Make sure you have write permissions to the output directory
   - Try running with elevated permissions if needed

4. **"API connection failed"**
   - Make sure the Flask server is running on port 5000
   - Check that no other service is using port 5000
   - Try restarting the web server

5. **"No output files generated"**
   - Check the GhostLink logs for encoding errors
   - Verify your input parameters are valid
   - Make sure the output directory is writable
   - Ensure GhostLink is properly installed via the Install tab

### Debug Mode

To see detailed logs, the server runs in debug mode by default. Check the terminal output for error messages and GhostLink processing logs.

## Development

### Modifying the Interface

The web interface is built with vanilla HTML, CSS, and JavaScript. To modify:

1. Edit `GhostWeb.html` for UI changes
2. Edit `ghostlink_api.py` for backend logic
3. Restart the server to see changes

### Adding New Features

1. **Frontend**: Add new form elements and JavaScript functions in `GhostWeb.html`
2. **Backend**: Add new API endpoints in `ghostlink_api.py`
3. **Integration**: Connect frontend to backend via fetch API calls

## License

This web interface is provided as-is to make GhostLink more accessible. The underlying GhostLink functionality is subject to its own license terms.
