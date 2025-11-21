"""
Video Frame Extractor
Extracts frames from video files for thumbnail selection
"""

import os
import sys
from typing import List, Optional
from pathlib import Path

# Try to import video processing libraries
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[WARNING] OpenCV not available. Install with: pip install opencv-python")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[WARNING] PIL/Pillow not available. Install with: pip install pillow")

def extract_frames_from_video(video_path: str, num_frames: int = 12, output_dir: Optional[str] = None) -> List[str]:
    """
    Extract frames from a video file.
    
    Args:
        video_path: Path to the video file
        num_frames: Number of frames to extract (default: 12)
        output_dir: Directory to save frames (optional, creates temp dir if not provided)
    
    Returns:
        List of paths to extracted frame images
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not CV2_AVAILABLE:
        raise ImportError("OpenCV is required for frame extraction. Install with: pip install opencv-python")
    
    # Create output directory if not provided
    if output_dir is None:
        video_name = Path(video_path).stem
        output_dir = os.path.join(os.path.dirname(video_path), f"{video_name}_frames")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    if total_frames == 0:
        cap.release()
        raise ValueError("Video file has no frames")
    
    # Calculate frame indices to extract (evenly spaced)
    frame_indices = []
    if num_frames >= total_frames:
        # Extract all frames
        frame_indices = list(range(total_frames))
    else:
        # Extract evenly spaced frames
        step = total_frames / (num_frames + 1)
        frame_indices = [int(step * (i + 1)) for i in range(num_frames)]
    
    extracted_frames = []
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check if this is a frame we want to extract
            if frame_count in frame_indices:
                # Generate filename
                timestamp = frame_count / fps if fps > 0 else frame_count
                frame_filename = f"frame_{frame_count:06d}_{timestamp:.2f}s.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                
                # Save frame as JPEG
                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                extracted_frames.append(frame_path)
            
            frame_count += 1
            
            # Stop if we've extracted all needed frames
            if len(extracted_frames) >= num_frames:
                break
        
        cap.release()
        
        # If we didn't get enough frames, try to get frames from the end
        if len(extracted_frames) < num_frames and total_frames > 0:
            # Go to the end and extract remaining frames
            remaining = num_frames - len(extracted_frames)
            end_frame_indices = [total_frames - 1 - i for i in range(remaining)]
            
            cap = cv2.VideoCapture(video_path)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count in end_frame_indices and frame_count not in frame_indices:
                    timestamp = frame_count / fps if fps > 0 else frame_count
                    frame_filename = f"frame_{frame_count:06d}_{timestamp:.2f}s.jpg"
                    frame_path = os.path.join(output_dir, frame_filename)
                    cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    extracted_frames.append(frame_path)
                
                frame_count += 1
                
                if len(extracted_frames) >= num_frames:
                    break
            
            cap.release()
        
        return sorted(extracted_frames)
    
    except Exception as e:
        if cap.isOpened():
            cap.release()
        raise Exception(f"Error extracting frames: {str(e)}")

def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        Duration in seconds
    """
    if not CV2_AVAILABLE:
        return 0.0
    
    if not os.path.exists(video_path):
        return 0.0
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.0
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0.0
    
    cap.release()
    return duration





