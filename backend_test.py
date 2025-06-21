#!/usr/bin/env python3
import requests
import time
import os
import json
from typing import Dict, Any, Optional

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

# Test YouTube URL (short video)
# Using a different URL as the original one is triggering bot detection
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up

# Test class for YouTube Downloader API
class YouTubeDownloaderTest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.download_id = None
        self.results = {
            "health_check": {"status": "Not tested", "details": ""},
            "video_info": {"status": "Not tested", "details": ""},
            "video_download": {"status": "Not tested", "details": ""},
            "download_status": {"status": "Not tested", "details": ""},
            "downloads_list": {"status": "Not tested", "details": ""},
            "stats": {"status": "Not tested", "details": ""}
        }
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("Starting YouTube Downloader API Tests...")
        print(f"Backend URL: {self.base_url}")
        
        # Run tests in order
        self.test_health_check()
        self.test_video_info()
        self.test_video_download()
        self.test_download_status()
        self.test_downloads_list()
        self.test_stats()
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def test_health_check(self):
        """Test the health check endpoint"""
        print("\n1. Testing health check endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "healthy":
                self.results["health_check"] = {
                    "status": "Passed",
                    "details": f"Health check successful: {data}"
                }
                print("✅ Health check passed")
            else:
                self.results["health_check"] = {
                    "status": "Failed",
                    "details": f"Health check returned unexpected status: {data}"
                }
                print("❌ Health check failed")
        except Exception as e:
            self.results["health_check"] = {
                "status": "Failed",
                "details": f"Health check request failed: {str(e)}"
            }
            print(f"❌ Health check failed: {str(e)}")
    
    def test_video_info(self):
        """Test video info extraction"""
        print("\n2. Testing video info extraction...")
        try:
            payload = {"url": TEST_VIDEO_URL}
            response = requests.post(f"{self.base_url}/api/video/info", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Check if essential video info is present
            if data.get("title") and data.get("uploader") and data.get("formats"):
                self.results["video_info"] = {
                    "status": "Passed",
                    "details": f"Video info extracted successfully: {data['title']} by {data['uploader']}"
                }
                print(f"✅ Video info extraction passed: '{data['title']}' by {data['uploader']}")
            else:
                self.results["video_info"] = {
                    "status": "Failed",
                    "details": f"Video info missing essential data: {data}"
                }
                print("❌ Video info extraction failed: Missing essential data")
        except Exception as e:
            self.results["video_info"] = {
                "status": "Failed",
                "details": f"Video info request failed: {str(e)}"
            }
            print(f"❌ Video info extraction failed: {str(e)}")
    
    def test_video_download(self):
        """Test video download initiation"""
        print("\n3. Testing video download initiation...")
        try:
            payload = {
                "url": TEST_VIDEO_URL,
                "quality": "best",
                "audio_only": False,
                "output_format": "mp4"
            }
            response = requests.post(f"{self.base_url}/api/video/download", json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("download_id") and data.get("status") == "started":
                self.download_id = data["download_id"]
                self.results["video_download"] = {
                    "status": "Passed",
                    "details": f"Download started successfully with ID: {self.download_id}"
                }
                print(f"✅ Video download initiation passed: ID {self.download_id}")
            else:
                self.results["video_download"] = {
                    "status": "Failed",
                    "details": f"Download initiation returned unexpected response: {data}"
                }
                print("❌ Video download initiation failed")
        except Exception as e:
            self.results["video_download"] = {
                "status": "Failed",
                "details": f"Download initiation request failed: {str(e)}"
            }
            print(f"❌ Video download initiation failed: {str(e)}")
    
    def test_download_status(self):
        """Test download status tracking"""
        print("\n4. Testing download status tracking...")
        if not self.download_id:
            self.results["download_status"] = {
                "status": "Skipped",
                "details": "No download ID available from previous test"
            }
            print("⚠️ Download status test skipped: No download ID available")
            return
        
        try:
            # Wait for download to start and check status multiple times
            max_attempts = 10
            for attempt in range(max_attempts):
                response = requests.get(f"{self.base_url}/api/video/status/{self.download_id}")
                response.raise_for_status()
                data = response.json()
                
                print(f"   Status check {attempt+1}/{max_attempts}: {data['status']} - Progress: {data['progress']:.1f}%")
                
                # If download completed or failed, break the loop
                if data['status'] in ['completed', 'failed']:
                    break
                
                # Wait before next check
                time.sleep(2)
            
            # Final status check
            if data['status'] in ['downloading', 'completed']:
                self.results["download_status"] = {
                    "status": "Passed",
                    "details": f"Download status tracking working: {data['status']} - Progress: {data['progress']:.1f}%"
                }
                print(f"✅ Download status tracking passed: Status '{data['status']}' with {data['progress']:.1f}% progress")
            else:
                self.results["download_status"] = {
                    "status": "Failed",
                    "details": f"Download status unexpected: {data}"
                }
                print(f"❌ Download status tracking failed: Status '{data['status']}'")
        except Exception as e:
            self.results["download_status"] = {
                "status": "Failed",
                "details": f"Download status request failed: {str(e)}"
            }
            print(f"❌ Download status tracking failed: {str(e)}")
    
    def test_downloads_list(self):
        """Test downloads list endpoint"""
        print("\n5. Testing downloads list...")
        try:
            response = requests.get(f"{self.base_url}/api/video/downloads")
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                self.results["downloads_list"] = {
                    "status": "Passed",
                    "details": f"Downloads list returned {len(data)} items"
                }
                print(f"✅ Downloads list passed: {len(data)} downloads found")
            else:
                self.results["downloads_list"] = {
                    "status": "Failed",
                    "details": f"Downloads list returned unexpected format: {data}"
                }
                print("❌ Downloads list failed: Unexpected format")
        except Exception as e:
            self.results["downloads_list"] = {
                "status": "Failed",
                "details": f"Downloads list request failed: {str(e)}"
            }
            print(f"❌ Downloads list failed: {str(e)}")
    
    def test_stats(self):
        """Test stats endpoint"""
        print("\n6. Testing stats endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/stats")
            response.raise_for_status()
            data = response.json()
            
            required_fields = ["total_downloads", "completed_downloads", "failed_downloads", 
                              "currently_downloading", "success_rate"]
            
            if all(field in data for field in required_fields):
                self.results["stats"] = {
                    "status": "Passed",
                    "details": f"Stats endpoint returned all required fields: {data}"
                }
                print(f"✅ Stats endpoint passed: {data}")
            else:
                self.results["stats"] = {
                    "status": "Failed",
                    "details": f"Stats endpoint missing required fields: {data}"
                }
                print("❌ Stats endpoint failed: Missing required fields")
        except Exception as e:
            self.results["stats"] = {
                "status": "Failed",
                "details": f"Stats endpoint request failed: {str(e)}"
            }
            print(f"❌ Stats endpoint failed: {str(e)}")
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n=== TEST SUMMARY ===")
        all_passed = True
        
        for test_name, result in self.results.items():
            status = result["status"]
            if status == "Failed":
                all_passed = False
                print(f"❌ {test_name}: {status} - {result['details']}")
            elif status == "Passed":
                print(f"✅ {test_name}: {status}")
            else:
                print(f"⚠️ {test_name}: {status}")
        
        if all_passed:
            print("\n🎉 All tests passed successfully!")
        else:
            print("\n⚠️ Some tests failed. See details above.")


if __name__ == "__main__":
    # Run all tests
    tester = YouTubeDownloaderTest(BACKEND_URL)
    results = tester.run_all_tests()
    
    # Save results to file
    with open('backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest results saved to backend_test_results.json")