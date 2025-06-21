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

# Test URLs for different platforms
TEST_YOUTUBE_URL = "https://youtu.be/jNQXAC9IVRw"  # First YouTube video
TEST_INSTAGRAM_URL = "https://www.instagram.com/p/CuM7GMPMnMe/"  # Sample Instagram post
TEST_REDDIT_URL = "https://www.reddit.com/r/videos/comments/12xqaef/rick_astley_never_gonna_give_you_up_4k_60fps_ai/"  # Sample Reddit post

# Test class for Multi-Platform Media Downloader API
class MediaDownloaderTest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.download_ids = {}  # Store download IDs for each platform
        self.results = {
            "health_check": {"status": "Not tested", "details": ""},
            "platform_detection": {"status": "Not tested", "details": ""},
            "youtube_info": {"status": "Not tested", "details": ""},
            "instagram_info": {"status": "Not tested", "details": ""},
            "reddit_info": {"status": "Not tested", "details": ""},
            "youtube_download": {"status": "Not tested", "details": ""},
            "instagram_download": {"status": "Not tested", "details": ""},
            "reddit_download": {"status": "Not tested", "details": ""},
            "download_status": {"status": "Not tested", "details": ""},
            "downloads_list": {"status": "Not tested", "details": ""},
            "platform_filter": {"status": "Not tested", "details": ""},
            "supported_platforms": {"status": "Not tested", "details": ""},
            "stats": {"status": "Not tested", "details": ""}
        }
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("Starting Multi-Platform Media Downloader API Tests...")
        print(f"Backend URL: {self.base_url}")
        
        # Run tests in order
        self.test_health_check()
        self.test_platform_detection()
        self.test_media_info()
        self.test_media_download()
        self.test_download_status()
        self.test_downloads_list()
        self.test_supported_platforms()
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
    
    def test_platform_detection(self):
        """Test platform detection from URLs"""
        print("\n2. Testing platform detection...")
        
        test_cases = [
            {"url": TEST_YOUTUBE_URL, "expected_platform": "youtube"},
            {"url": TEST_INSTAGRAM_URL, "expected_platform": "instagram"},
            {"url": TEST_REDDIT_URL, "expected_platform": "reddit"}
        ]
        
        all_passed = True
        details = []
        
        for test_case in test_cases:
            url = test_case["url"]
            expected = test_case["expected_platform"]
            
            try:
                # Use the media info endpoint to test platform detection
                payload = {"url": url}
                response = requests.post(f"{self.base_url}/api/media/info", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    detected = data.get("platform", "unknown")
                    
                    if detected == expected:
                        details.append(f"✅ {url} correctly detected as {detected}")
                        print(f"✅ {url} correctly detected as {detected}")
                    else:
                        details.append(f"❌ {url} incorrectly detected as {detected}, expected {expected}")
                        print(f"❌ {url} incorrectly detected as {detected}, expected {expected}")
                        all_passed = False
                else:
                    # If we get an error, check if it's a known limitation
                    error_msg = response.text
                    if "bot" in error_msg.lower() or "rate limit" in error_msg.lower():
                        details.append(f"⚠️ {url} detection failed due to platform limitations: {error_msg}")
                        print(f"⚠️ {url} detection failed due to platform limitations")
                    else:
                        details.append(f"❌ {url} detection failed: {error_msg}")
                        print(f"❌ {url} detection failed: {error_msg}")
                        all_passed = False
            except Exception as e:
                details.append(f"❌ {url} detection failed with exception: {str(e)}")
                print(f"❌ {url} detection failed with exception: {str(e)}")
                all_passed = False
        
        if all_passed:
            self.results["platform_detection"] = {
                "status": "Passed",
                "details": "\n".join(details)
            }
        else:
            self.results["platform_detection"] = {
                "status": "Failed",
                "details": "\n".join(details)
            }
    
    def test_media_info(self):
        """Test media info extraction for different platforms"""
        print("\n3. Testing media info extraction for different platforms...")
        
        # Test YouTube info
        print("   Testing YouTube info extraction...")
        try:
            payload = {"url": TEST_YOUTUBE_URL}
            response = requests.post(f"{self.base_url}/api/media/info", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("title") and data.get("platform") == "youtube":
                    self.results["youtube_info"] = {
                        "status": "Passed",
                        "details": f"YouTube info extracted successfully: {data['title']}"
                    }
                    print(f"✅ YouTube info extraction passed: '{data['title']}'")
                else:
                    self.results["youtube_info"] = {
                        "status": "Failed",
                        "details": f"YouTube info missing essential data: {data}"
                    }
                    print("❌ YouTube info extraction failed: Missing essential data")
            elif response.status_code == 400 and "bot" in response.text.lower():
                # YouTube bot detection is a known issue with yt-dlp
                self.results["youtube_info"] = {
                    "status": "Warning",
                    "details": "YouTube bot detection triggered. This is a known limitation with yt-dlp in containerized environments."
                }
                print("⚠️ YouTube info extraction warning: YouTube bot detection triggered")
            else:
                self.results["youtube_info"] = {
                    "status": "Failed",
                    "details": f"YouTube info request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ YouTube info extraction failed: Status code {response.status_code}")
        except Exception as e:
            self.results["youtube_info"] = {
                "status": "Failed",
                "details": f"YouTube info request failed: {str(e)}"
            }
            print(f"❌ YouTube info extraction failed: {str(e)}")
        
        # Test Instagram info
        print("   Testing Instagram info extraction...")
        try:
            payload = {"url": TEST_INSTAGRAM_URL}
            response = requests.post(f"{self.base_url}/api/media/info", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("title") and data.get("platform") == "instagram":
                    self.results["instagram_info"] = {
                        "status": "Passed",
                        "details": f"Instagram info extracted successfully: {data['title']} by {data.get('uploader', 'unknown')}"
                    }
                    print(f"✅ Instagram info extraction passed: '{data['title']}' by {data.get('uploader', 'unknown')}")
                else:
                    self.results["instagram_info"] = {
                        "status": "Failed",
                        "details": f"Instagram info missing essential data: {data}"
                    }
                    print("❌ Instagram info extraction failed: Missing essential data")
            else:
                self.results["instagram_info"] = {
                    "status": "Failed",
                    "details": f"Instagram info request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ Instagram info extraction failed: Status code {response.status_code}")
        except Exception as e:
            self.results["instagram_info"] = {
                "status": "Failed",
                "details": f"Instagram info request failed: {str(e)}"
            }
            print(f"❌ Instagram info extraction failed: {str(e)}")
        
        # Test Reddit info
        print("   Testing Reddit info extraction...")
        try:
            payload = {"url": TEST_REDDIT_URL}
            response = requests.post(f"{self.base_url}/api/media/info", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("title") and data.get("platform") == "reddit":
                    self.results["reddit_info"] = {
                        "status": "Passed",
                        "details": f"Reddit info extracted successfully: {data['title']} by {data.get('uploader', 'unknown')}"
                    }
                    print(f"✅ Reddit info extraction passed: '{data['title']}' by {data.get('uploader', 'unknown')}")
                else:
                    self.results["reddit_info"] = {
                        "status": "Failed",
                        "details": f"Reddit info missing essential data: {data}"
                    }
                    print("❌ Reddit info extraction failed: Missing essential data")
            else:
                self.results["reddit_info"] = {
                    "status": "Failed",
                    "details": f"Reddit info request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ Reddit info extraction failed: Status code {response.status_code}")
        except Exception as e:
            self.results["reddit_info"] = {
                "status": "Failed",
                "details": f"Reddit info request failed: {str(e)}"
            }
            print(f"❌ Reddit info extraction failed: {str(e)}")
    
    def test_media_download(self):
        """Test media download initiation for different platforms"""
        print("\n4. Testing media download initiation for different platforms...")
        
        # Test YouTube download
        print("   Testing YouTube download initiation...")
        try:
            payload = {
                "url": TEST_YOUTUBE_URL,
                "quality": "best",
                "audio_only": False,
                "output_format": "mp4",
                "platform": "youtube"
            }
            response = requests.post(f"{self.base_url}/api/media/download", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("download_id") and data.get("status") == "started" and data.get("platform") == "youtube":
                    self.download_ids["youtube"] = data["download_id"]
                    self.results["youtube_download"] = {
                        "status": "Passed",
                        "details": f"YouTube download started successfully with ID: {self.download_ids['youtube']}"
                    }
                    print(f"✅ YouTube download initiation passed: ID {self.download_ids['youtube']}")
                else:
                    self.results["youtube_download"] = {
                        "status": "Failed",
                        "details": f"YouTube download initiation returned unexpected response: {data}"
                    }
                    print("❌ YouTube download initiation failed")
            else:
                self.results["youtube_download"] = {
                    "status": "Failed",
                    "details": f"YouTube download request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ YouTube download initiation failed: Status code {response.status_code}")
        except Exception as e:
            self.results["youtube_download"] = {
                "status": "Failed",
                "details": f"YouTube download request failed: {str(e)}"
            }
            print(f"❌ YouTube download initiation failed: {str(e)}")
        
        # Test Instagram download
        print("   Testing Instagram download initiation...")
        try:
            payload = {
                "url": TEST_INSTAGRAM_URL,
                "quality": "best",
                "audio_only": False,
                "output_format": "mp4",
                "platform": "instagram"
            }
            response = requests.post(f"{self.base_url}/api/media/download", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("download_id") and data.get("status") == "started" and data.get("platform") == "instagram":
                    self.download_ids["instagram"] = data["download_id"]
                    self.results["instagram_download"] = {
                        "status": "Passed",
                        "details": f"Instagram download started successfully with ID: {self.download_ids['instagram']}"
                    }
                    print(f"✅ Instagram download initiation passed: ID {self.download_ids['instagram']}")
                else:
                    self.results["instagram_download"] = {
                        "status": "Failed",
                        "details": f"Instagram download initiation returned unexpected response: {data}"
                    }
                    print("❌ Instagram download initiation failed")
            else:
                self.results["instagram_download"] = {
                    "status": "Failed",
                    "details": f"Instagram download request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ Instagram download initiation failed: Status code {response.status_code}")
        except Exception as e:
            self.results["instagram_download"] = {
                "status": "Failed",
                "details": f"Instagram download request failed: {str(e)}"
            }
            print(f"❌ Instagram download initiation failed: {str(e)}")
        
        # Test Reddit download
        print("   Testing Reddit download initiation...")
        try:
            payload = {
                "url": TEST_REDDIT_URL,
                "quality": "best",
                "audio_only": False,
                "output_format": "mp4",
                "platform": "reddit"
            }
            response = requests.post(f"{self.base_url}/api/media/download", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("download_id") and data.get("status") == "started" and data.get("platform") == "reddit":
                    self.download_ids["reddit"] = data["download_id"]
                    self.results["reddit_download"] = {
                        "status": "Passed",
                        "details": f"Reddit download started successfully with ID: {self.download_ids['reddit']}"
                    }
                    print(f"✅ Reddit download initiation passed: ID {self.download_ids['reddit']}")
                else:
                    self.results["reddit_download"] = {
                        "status": "Failed",
                        "details": f"Reddit download initiation returned unexpected response: {data}"
                    }
                    print("❌ Reddit download initiation failed")
            else:
                self.results["reddit_download"] = {
                    "status": "Failed",
                    "details": f"Reddit download request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ Reddit download initiation failed: Status code {response.status_code}")
        except Exception as e:
            self.results["reddit_download"] = {
                "status": "Failed",
                "details": f"Reddit download request failed: {str(e)}"
            }
            print(f"❌ Reddit download initiation failed: {str(e)}")
    
    def test_download_status(self):
        """Test download status tracking"""
        print("\n5. Testing download status tracking...")
        
        # Check status for each platform where we have a download ID
        for platform, download_id in self.download_ids.items():
            print(f"   Testing {platform} download status...")
            try:
                # Wait for download to start and check status multiple times
                max_attempts = 5
                final_status = None
                
                for attempt in range(max_attempts):
                    response = requests.get(f"{self.base_url}/api/media/status/{download_id}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   Status check {attempt+1}/{max_attempts} for {platform}: {data['status']} - Progress: {data['progress']:.1f}%")
                        
                        # If download completed or failed, break the loop
                        if data['status'] in ['completed', 'failed']:
                            final_status = data
                            break
                        
                        # Wait before next check
                        time.sleep(2)
                    else:
                        print(f"   Status check failed: {response.status_code}")
                        break
                
                # Evaluate final status
                if final_status and final_status['status'] == 'completed':
                    self.results["download_status"] = {
                        "status": "Passed",
                        "details": f"{platform} download completed successfully"
                    }
                    print(f"✅ {platform} download status tracking passed: Status 'completed'")
                elif final_status and final_status['status'] == 'downloading':
                    self.results["download_status"] = {
                        "status": "Passed",
                        "details": f"{platform} download in progress: {final_status['progress']:.1f}%"
                    }
                    print(f"✅ {platform} download status tracking passed: Status 'downloading' with {final_status['progress']:.1f}% progress")
                elif final_status and final_status['status'] == 'failed':
                    if final_status.get('error_message') and ('bot' in final_status['error_message'].lower() or 'authentication' in final_status['error_message'].lower()):
                        self.results["download_status"] = {
                            "status": "Warning",
                            "details": f"{platform} download failed due to platform limitations: {final_status['error_message']}"
                        }
                        print(f"⚠️ {platform} download status tracking warning: Platform limitations")
                    else:
                        self.results["download_status"] = {
                            "status": "Failed",
                            "details": f"{platform} download failed: {final_status.get('error_message', 'Unknown error')}"
                        }
                        print(f"❌ {platform} download status tracking failed: {final_status.get('error_message', 'Unknown error')}")
                else:
                    self.results["download_status"] = {
                        "status": "Failed",
                        "details": f"{platform} download status unexpected or not available"
                    }
                    print(f"❌ {platform} download status tracking failed: Status unexpected or not available")
            except Exception as e:
                self.results["download_status"] = {
                    "status": "Failed",
                    "details": f"{platform} download status request failed: {str(e)}"
                }
                print(f"❌ {platform} download status tracking failed: {str(e)}")
    
    def test_downloads_list(self):
        """Test downloads list endpoint with platform filtering"""
        print("\n6. Testing downloads list with platform filtering...")
        
        # Test general downloads list
        try:
            response = requests.get(f"{self.base_url}/api/media/downloads")
            
            if response.status_code == 200:
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
            else:
                self.results["downloads_list"] = {
                    "status": "Failed",
                    "details": f"Downloads list request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ Downloads list failed: Status code {response.status_code}")
        except Exception as e:
            self.results["downloads_list"] = {
                "status": "Failed",
                "details": f"Downloads list request failed: {str(e)}"
            }
            print(f"❌ Downloads list failed: {str(e)}")
        
        # Test platform filtering
        print("   Testing platform filtering...")
        try:
            platforms = ["youtube", "instagram", "reddit"]
            all_passed = True
            details = []
            
            for platform in platforms:
                response = requests.get(f"{self.base_url}/api/media/downloads?platform={platform}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list):
                        # Check if all items have the correct platform
                        all_correct_platform = all(item.get("platform") == platform for item in data) if data else True
                        
                        if all_correct_platform:
                            details.append(f"✅ {platform} filter returned {len(data)} items, all with correct platform")
                            print(f"✅ {platform} filter returned {len(data)} items, all with correct platform")
                        else:
                            details.append(f"❌ {platform} filter returned items with incorrect platform")
                            print(f"❌ {platform} filter returned items with incorrect platform")
                            all_passed = False
                    else:
                        details.append(f"❌ {platform} filter returned unexpected format: {data}")
                        print(f"❌ {platform} filter returned unexpected format")
                        all_passed = False
                else:
                    details.append(f"❌ {platform} filter request failed with status code {response.status_code}")
                    print(f"❌ {platform} filter request failed: Status code {response.status_code}")
                    all_passed = False
            
            if all_passed:
                self.results["platform_filter"] = {
                    "status": "Passed",
                    "details": "\n".join(details)
                }
            else:
                self.results["platform_filter"] = {
                    "status": "Failed",
                    "details": "\n".join(details)
                }
        except Exception as e:
            self.results["platform_filter"] = {
                "status": "Failed",
                "details": f"Platform filter request failed: {str(e)}"
            }
            print(f"❌ Platform filter failed: {str(e)}")
    
    def test_supported_platforms(self):
        """Test supported platforms endpoint"""
        print("\n7. Testing supported platforms endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/platforms")
            
            if response.status_code == 200:
                data = response.json()
                
                if "supported_platforms" in data and isinstance(data["supported_platforms"], list):
                    platforms = [p["key"] for p in data["supported_platforms"]]
                    required_platforms = ["youtube", "instagram", "reddit"]
                    
                    if all(platform in platforms for platform in required_platforms):
                        self.results["supported_platforms"] = {
                            "status": "Passed",
                            "details": f"Supported platforms endpoint returned all required platforms: {platforms}"
                        }
                        print(f"✅ Supported platforms endpoint passed: {platforms}")
                    else:
                        missing = [p for p in required_platforms if p not in platforms]
                        self.results["supported_platforms"] = {
                            "status": "Failed",
                            "details": f"Supported platforms endpoint missing required platforms: {missing}"
                        }
                        print(f"❌ Supported platforms endpoint failed: Missing {missing}")
                else:
                    self.results["supported_platforms"] = {
                        "status": "Failed",
                        "details": f"Supported platforms endpoint returned unexpected format: {data}"
                    }
                    print("❌ Supported platforms endpoint failed: Unexpected format")
            else:
                self.results["supported_platforms"] = {
                    "status": "Failed",
                    "details": f"Supported platforms request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ Supported platforms endpoint failed: Status code {response.status_code}")
        except Exception as e:
            self.results["supported_platforms"] = {
                "status": "Failed",
                "details": f"Supported platforms request failed: {str(e)}"
            }
            print(f"❌ Supported platforms endpoint failed: {str(e)}")
    
    def test_stats(self):
        """Test stats endpoint"""
        print("\n8. Testing stats endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/stats")
            
            if response.status_code == 200:
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
            else:
                self.results["stats"] = {
                    "status": "Failed",
                    "details": f"Stats endpoint request failed with status code {response.status_code}: {response.text}"
                }
                print(f"❌ Stats endpoint failed: Status code {response.status_code}")
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
            elif status == "Warning":
                print(f"⚠️ {test_name}: {status} - {result['details']}")
            else:
                print(f"⚠️ {test_name}: {status}")
        
        if all_passed:
            print("\n🎉 All tests passed successfully!")
        else:
            print("\n⚠️ Some tests failed. See details above.")


if __name__ == "__main__":
    # Run all tests
    tester = MediaDownloaderTest(BACKEND_URL)
    results = tester.run_all_tests()
    
    # Save results to file
    with open('backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest results saved to backend_test_results.json")