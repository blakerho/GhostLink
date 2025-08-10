#!/usr/bin/env python3
"""
GhostLink Web API Backend
Connects the web UI to the actual GhostLink Python application
"""

import os
import sys
import tempfile
import shutil
import subprocess
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import werkzeug

# Add GhostLink to Python path (ghostFace is inside GhostLink folder)
ghostlink_path = Path(__file__).parent.parent
sys.path.insert(0, str(ghostlink_path))

# Import GhostLink modules (with fallback)
try:
    from ghostlink import __main__ as ghostlink_main
    from ghostlink import decoder as ghostlink_decoder
    GHOSTLINK_AVAILABLE = True
except ImportError:
    GHOSTLINK_AVAILABLE = False
    ghostlink_main = None
    ghostlink_decoder = None

app = Flask(__name__)
CORS(app)  # Enable CORS for web interface

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GhostLinkAPI:
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ghostlink_web_"))
        logger.info(f"Initialized GhostLink API with temp directory: {self.temp_dir}")
    
    def encode_text(self, text, output_dir, **kwargs):
        """Encode text using GhostLink"""
        if not GHOSTLINK_AVAILABLE:
            return {"success": False, "error": "GhostLink not installed. Please install it first using the Install tab."}
        
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Prepare arguments for GhostLink
            args = self._prepare_encode_args("text", text, str(output_path), **kwargs)
            
            # Run encoding
            result = ghostlink_main.main_with_args(args)
            
            if result == 0:
                # Find the generated file
                wav_files = list(output_path.glob("*.wav"))
                if wav_files:
                    return {"success": True, "file": str(wav_files[0])}
                else:
                    return {"success": False, "error": "No output file generated"}
            else:
                return {"success": False, "error": f"Encoding failed with code {result}"}
                
        except Exception as e:
            logger.error(f"Encode error: {e}")
            return {"success": False, "error": str(e)}
    
    def encode_file(self, file_path, output_dir, **kwargs):
        """Encode a file using GhostLink"""
        if not GHOSTLINK_AVAILABLE:
            return {"success": False, "error": "GhostLink not installed. Please install it first using the Install tab."}
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            args = self._prepare_encode_args("file", file_path, str(output_path), **kwargs)
            result = ghostlink_main.main_with_args(args)
            
            if result == 0:
                wav_files = list(output_path.glob("*.wav"))
                if wav_files:
                    return {"success": True, "file": str(wav_files[0])}
                else:
                    return {"success": False, "error": "No output file generated"}
            else:
                return {"success": False, "error": f"Encoding failed with code {result}"}
                
        except Exception as e:
            logger.error(f"Encode file error: {e}")
            return {"success": False, "error": str(e)}
    
    def encode_directory(self, input_dir, output_dir, **kwargs):
        """Encode all text files in a directory using GhostLink"""
        if not GHOSTLINK_AVAILABLE:
            return {"success": False, "error": "GhostLink not installed. Please install it first using the Install tab."}
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            args = self._prepare_encode_args("dir", input_dir, str(output_path), **kwargs)
            result = ghostlink_main.main_with_args(args)
            
            if result == 0:
                wav_files = list(output_path.glob("*.wav"))
                return {"success": True, "files": [str(f) for f in wav_files]}
            else:
                return {"success": False, "error": f"Encoding failed with code {result}"}
                
        except Exception as e:
            logger.error(f"Encode directory error: {e}")
            return {"success": False, "error": str(e)}
    
    def decode_file(self, file_path, **kwargs):
        """Decode a WAV file using GhostLink"""
        if not GHOSTLINK_AVAILABLE:
            return {"success": False, "error": "GhostLink not installed. Please install it first using the Install tab."}
        
        try:
            args = self._prepare_decode_args(file_path, **kwargs)
            result = ghostlink_decoder.main_with_args(args)
            
            if result == 0:
                # The decoder prints to stdout, so we need to capture it
                # For now, we'll use subprocess to capture output
                cmd = [
                    sys.executable, "-m", "ghostlink.decoder",
                    file_path,
                    "--verbose" if kwargs.get("verbose", False) else ""
                ]
                
                # Add other arguments
                if kwargs.get("baud"):
                    cmd.extend(["--baud", str(kwargs["baud"])])
                if kwargs.get("preamble"):
                    cmd.extend(["--preamble", str(kwargs["preamble"])])
                if kwargs.get("sparse"):
                    cmd.append("--sparse")
                if kwargs.get("mix_profile"):
                    cmd.extend(["--mix-profile", kwargs["mix_profile"]])
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ghostlink_path))
                
                if result.returncode == 0:
                    return {"success": True, "decoded_text": result.stdout.strip()}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            else:
                return {"success": False, "error": f"Decoding failed with code {result}"}
                
        except Exception as e:
            logger.error(f"Decode error: {e}")
            return {"success": False, "error": str(e)}
    
    def _prepare_encode_args(self, mode, input_arg, output_dir, **kwargs):
        """Prepare arguments for GhostLink encoding"""
        args = type('Args', (), {})()
        args.mode = mode
        args.input = input_arg
        args.outdir = output_dir
        args.samplerate = kwargs.get("samplerate", 48000)
        args.baud = kwargs.get("baud", 90)
        args.amp = kwargs.get("amp", 0.06)
        args.dense = kwargs.get("dense", True)
        args.sparse = kwargs.get("sparse", False)
        args.mix_profile = kwargs.get("mix_profile", "streaming")
        args.gap = kwargs.get("gap", 0)
        args.preamble = kwargs.get("preamble", 0.8)
        args.interleave = kwargs.get("interleave", 4)
        args.repeats = kwargs.get("repeats", 2)
        args.ramp = kwargs.get("ramp", 5)
        args.out_name = kwargs.get("out_name")
        args.verbose = kwargs.get("verbose", True)
        return args
    
    def _prepare_decode_args(self, file_path, **kwargs):
        """Prepare arguments for GhostLink decoding"""
        args = type('Args', (), {})()
        args.wav = file_path
        args.baud = kwargs.get("baud", 90)
        args.dense = kwargs.get("dense", True)
        args.sparse = kwargs.get("sparse", False)
        args.mix_profile = kwargs.get("mix_profile", "streaming")
        args.preamble = kwargs.get("preamble", 0.8)
        args.interleave = kwargs.get("interleave", 4)
        args.repeats = kwargs.get("repeats", 2)
        args.verbose = kwargs.get("verbose", True)
        return args

# Initialize the API
ghostlink_api = GhostLinkAPI()

@app.route('/api/encode', methods=['POST'])
def encode():
    """Encode text, file, or directory"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        mode = data.get("mode")
        ghostlink_dir = data.get("ghostlink_dir")
        output_dir = data.get("output_dir")
        
        if not all([mode, ghostlink_dir, output_dir]):
            return jsonify({"success": False, "error": "Missing required parameters"}), 400
        
        # Extract encoding parameters
        params = {
            "samplerate": data.get("samplerate", 48000),
            "baud": data.get("baud", 90),
            "amp": data.get("amp", 0.06),
            "dense": data.get("fsk_mode") == "dense",
            "sparse": data.get("fsk_mode") == "sparse",
            "mix_profile": data.get("mix_profile", "streaming"),
            "gap": data.get("gap", 0),
            "preamble": data.get("preamble", 0.8),
            "interleave": data.get("interleave", 4),
            "repeats": data.get("repeats", 2),
            "ramp": data.get("ramp", 5),
            "out_name": data.get("custom_filename"),
            "verbose": True
        }
        
        if mode == "text":
            text = data.get("text")
            if not text:
                return jsonify({"success": False, "error": "No text provided"}), 400
            result = ghostlink_api.encode_text(text, output_dir, **params)
            
        elif mode == "file":
            file_path = data.get("file_path")
            if not file_path:
                return jsonify({"success": False, "error": "No file path provided"}), 400
            result = ghostlink_api.encode_file(file_path, output_dir, **params)
            
        elif mode == "dir":
            input_dir = data.get("input_dir")
            if not input_dir:
                return jsonify({"success": False, "error": "No input directory provided"}), 400
            result = ghostlink_api.encode_directory(input_dir, output_dir, **params)
            
        else:
            return jsonify({"success": False, "error": f"Unknown mode: {mode}"}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Encode API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/decode', methods=['POST'])
def decode():
    """Decode a WAV file"""
    try:
        # Handle file upload
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Save uploaded file to temp directory
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="ghostlink_decode_"))
        file_path = temp_dir / file.filename
        file.save(str(file_path))
        
        ghostlink_dir = request.form.get("ghostlink_dir")
        
        if not ghostlink_dir:
            return jsonify({"success": False, "error": "Missing GhostLink directory"}), 400
        
        # Extract decoding parameters
        params = {
            "baud": float(request.form.get("baud", 90)),
            "dense": request.form.get("fsk_mode") == "dense",
            "sparse": request.form.get("fsk_mode") == "sparse",
            "mix_profile": request.form.get("mix_profile", "streaming"),
            "preamble": float(request.form.get("preamble", 0.8)),
            "interleave": int(request.form.get("interleave", 4)),
            "repeats": int(request.form.get("repeats", 2)),
            "verbose": True
        }
        
        result = ghostlink_api.decode_file(str(file_path), **params)
        
        # Clean up temp file
        try:
            file_path.unlink()
            temp_dir.rmdir()
        except:
            pass
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Decode API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def batch():
    """Batch processing"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        batch_mode = data.get("mode")
        input_dir = data.get("input_dir")
        output_dir = data.get("output_dir")
        ghostlink_dir = data.get("ghostlink_dir")
        
        if not all([batch_mode, input_dir, output_dir, ghostlink_dir]):
            return jsonify({"success": False, "error": "Missing required parameters"}), 400
        
        # For now, batch processing just encodes all files in the directory
        if batch_mode == "encode-multiple":
            result = ghostlink_api.encode_directory(input_dir, output_dir)
        else:
            return jsonify({"success": False, "error": f"Unsupported batch mode: {batch_mode}"}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Batch API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "ghostlink_path": str(ghostlink_path)})

@app.route('/api/install/check', methods=['GET'])
def check_installation():
    """Check if GhostLink and dependencies are installed"""
    try:
        # Check if GhostLink is available
        import ghostlink
        ghostlink_installed = True
    except ImportError:
        ghostlink_installed = False
    
    # Check if Flask dependencies are available
    try:
        import flask
        import flask_cors
        flask_installed = True
    except ImportError:
        flask_installed = False
    
    # Check if we can import the main modules
    modules_available = GHOSTLINK_AVAILABLE
    
    return jsonify({
        "ghostlink_installed": ghostlink_installed,
        "flask_installed": flask_installed,
        "modules_available": modules_available,
        "ghostlink_path": str(ghostlink_path)
    })

@app.route('/api/install/ghostlink', methods=['POST'])
def install_ghostlink():
    """Install GhostLink package"""
    try:
        # Change to GhostLink directory and install
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], cwd=str(ghostlink_path), capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({"success": True, "message": "GhostLink installed successfully"})
        else:
            return jsonify({"success": False, "error": result.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/install/dependencies', methods=['POST'])
def install_dependencies():
    """Install Flask and other web dependencies"""
    try:
        # Get the path to requirements_api.txt
        requirements_path = Path(__file__).parent / "requirements_api.txt"
        
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({"success": True, "message": "Dependencies installed successfully"})
        else:
            return jsonify({"success": False, "error": result.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/install/all', methods=['POST'])
def install_all():
    """Install both GhostLink and dependencies"""
    try:
        # Install dependencies first
        deps_result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(Path(__file__).parent / "requirements_api.txt")
        ], capture_output=True, text=True)
        
        if deps_result.returncode != 0:
            return jsonify({"success": False, "error": f"Dependencies failed: {deps_result.stderr}"})
        
        # Install GhostLink
        ghostlink_result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], cwd=str(ghostlink_path), capture_output=True, text=True)
        
        if ghostlink_result.returncode == 0:
            return jsonify({"success": True, "message": "All components installed successfully"})
        else:
            return jsonify({"success": False, "error": f"GhostLink failed: {ghostlink_result.stderr}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print("Starting GhostLink Web API...")
    print(f"GhostLink path: {ghostlink_path}")
    print(f"Temp directory: {ghostlink_api.temp_dir}")
    print("API will be available at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
