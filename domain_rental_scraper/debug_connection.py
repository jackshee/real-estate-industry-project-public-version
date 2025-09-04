#!/usr/bin/env python3
"""
Comprehensive debugging script for Domain.com.au connection issues
"""

import requests
from bs4 import BeautifulSoup
import time
import ssl
import urllib3
from urllib.parse import urlparse
import json

# Disable SSL warnings for debugging
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_basic_connectivity():
    """Test basic internet connectivity"""
    print("=== Testing Basic Connectivity ===")

    test_urls = [
        "https://httpbin.org/get",
        "https://www.google.com",
        "https://www.domain.com.au",
    ]

    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")


def test_domain_specific():
    """Test Domain.com.au specific connectivity"""
    print("\n=== Testing Domain.com.au Specific ===")

    base_url = "https://www.domain.com.au"
    test_urls = [
        base_url,
        f"{base_url}/",
        f"{base_url}/rent/",
        f"{base_url}/rent/?sort=price-asc&page=1",
    ]

    headers_list = [
        # Basic headers
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        },
        # More complete headers
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        },
        # Mobile headers
        {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
        },
    ]

    for url in test_urls:
        print(f"\nTesting: {url}")
        for i, headers in enumerate(headers_list):
            try:
                print(f"  Headers set {i+1}: ", end="")
                response = requests.get(url, headers=headers, timeout=15, verify=True)
                print(
                    f"✅ Status {response.status_code}, Length: {len(response.content)}"
                )

                if response.status_code == 200:
                    # Save successful response for analysis
                    with open(
                        f"successful_response_{i+1}.html", "w", encoding="utf-8"
                    ) as f:
                        f.write(response.text)
                    print(f"    Saved response to successful_response_{i+1}.html")

                    # Quick analysis
                    soup = BeautifulSoup(response.content, "html.parser")
                    title = soup.find("title")
                    print(
                        f"    Page title: {title.get_text() if title else 'No title'}"
                    )

                    # Look for property-related content
                    price_elements = soup.find_all(
                        text=lambda text: text and "$" in text
                    )
                    print(f"    Found {len(price_elements)} elements with '$'")

                    if price_elements:
                        print("    Sample price elements:")
                        for j, price in enumerate(price_elements[:3]):
                            print(f"      {j+1}: {price.strip()[:50]}...")

                    break  # If successful, don't try other header sets

            except requests.exceptions.Timeout:
                print("❌ Timeout")
            except requests.exceptions.ConnectionError as e:
                print(f"❌ Connection Error: {e}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Request Error: {e}")
            except Exception as e:
                print(f"❌ Unexpected Error: {e}")


def test_with_session():
    """Test with persistent session"""
    print("\n=== Testing with Persistent Session ===")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )

    # First, try to get the main page
    try:
        print("Getting main domain page...")
        response = session.get("https://www.domain.com.au", timeout=15)
        print(f"Main page: Status {response.status_code}")

        if response.status_code == 200:
            # Now try the rental page
            print("Getting rental page...")
            rental_response = session.get(
                "https://www.domain.com.au/rent/?sort=price-asc&page=1", timeout=15
            )
            print(
                f"Rental page: Status {rental_response.status_code}, Length: {len(rental_response.content)}"
            )

            if rental_response.status_code == 200:
                with open("rental_page_response.html", "w", encoding="utf-8") as f:
                    f.write(rental_response.text)
                print("Saved rental page response to rental_page_response.html")

                # Analyze the response
                soup = BeautifulSoup(rental_response.content, "html.parser")

                # Look for common patterns
                print("\nAnalyzing page structure:")

                # Check for JavaScript-rendered content indicators
                scripts = soup.find_all("script")
                print(f"Found {len(scripts)} script tags")

                # Look for data attributes
                data_elements = soup.find_all(attrs={"data-testid": True})
                print(f"Found {len(data_elements)} elements with data-testid")

                if data_elements:
                    testids = [elem.get("data-testid") for elem in data_elements[:10]]
                    print(f"Sample data-testids: {testids}")

                # Look for property-related classes
                property_divs = soup.find_all(
                    "div",
                    class_=lambda x: x
                    and any(
                        keyword in x.lower()
                        for keyword in ["property", "listing", "card", "result", "rent"]
                    ),
                )
                print(f"Found {len(property_divs)} divs with property-related classes")

                # Check for specific Domain.com.au patterns
                domain_specific = soup.find_all(
                    "div", class_=lambda x: x and "domain" in x.lower()
                )
                print(f"Found {len(domain_specific)} divs with 'domain' in class")

    except Exception as e:
        print(f"Session test failed: {e}")


def test_ssl_and_certificates():
    """Test SSL and certificate issues"""
    print("\n=== Testing SSL and Certificates ===")

    try:
        # Test SSL context
        context = ssl.create_default_context()
        print("✅ SSL context created successfully")

        # Test certificate verification
        response = requests.get("https://www.domain.com.au", verify=True, timeout=10)
        print(f"✅ Certificate verification successful: Status {response.status_code}")

    except ssl.SSLError as e:
        print(f"❌ SSL Error: {e}")
    except Exception as e:
        print(f"❌ Certificate test failed: {e}")


def test_proxy_and_network():
    """Test network configuration"""
    print("\n=== Testing Network Configuration ===")

    # Test DNS resolution
    try:
        import socket

        ip = socket.gethostbyname("www.domain.com.au")
        print(f"✅ DNS resolution successful: {ip}")
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")

    # Test if we're behind a proxy
    import os

    proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
    for var in proxy_vars:
        if var in os.environ:
            print(f"⚠️  Proxy detected: {var}={os.environ[var]}")


def analyze_saved_responses():
    """Analyze any saved HTML responses"""
    print("\n=== Analyzing Saved Responses ===")

    import glob

    html_files = glob.glob("*.html")

    for file in html_files:
        print(f"\nAnalyzing {file}:")
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            soup = BeautifulSoup(content, "html.parser")

            # Basic stats
            print(f"  File size: {len(content)} characters")
            print(
                f"  Title: {soup.find('title').get_text() if soup.find('title') else 'No title'}"
            )

            # Look for error indicators
            error_indicators = [
                "error",
                "blocked",
                "access denied",
                "forbidden",
                "not found",
            ]
            content_lower = content.lower()
            for indicator in error_indicators:
                if indicator in content_lower:
                    print(f"  ⚠️  Found error indicator: '{indicator}'")

            # Look for JavaScript frameworks
            js_frameworks = ["react", "vue", "angular", "next.js", "nuxt"]
            for framework in js_frameworks:
                if framework in content_lower:
                    print(f"  📱 JavaScript framework detected: {framework}")

            # Look for property data
            price_count = content.count("$")
            print(f"  💰 Found {price_count} '$' symbols")

            if price_count > 0:
                # Extract some price examples
                import re

                prices = re.findall(r"\$[\d,]+(?:\s+per\s+(?:week|month))?", content)
                if prices:
                    print(f"  Sample prices: {prices[:5]}")

        except Exception as e:
            print(f"  ❌ Error analyzing {file}: {e}")


def main():
    """Run all debugging tests"""
    print("🔍 Starting comprehensive debugging of Domain.com.au connection...")

    test_basic_connectivity()
    test_domain_specific()
    test_with_session()
    test_ssl_and_certificates()
    test_proxy_and_network()
    analyze_saved_responses()

    print("\n🏁 Debugging complete!")
    print("\nNext steps:")
    print("1. Check the saved HTML files to see what we actually received")
    print("2. Look for JavaScript-rendered content that might need Selenium")
    print("3. Check if the site requires specific headers or cookies")
    print("4. Consider if the site has anti-bot protection")


if __name__ == "__main__":
    main()
