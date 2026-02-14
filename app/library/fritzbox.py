#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
from fritzconnection import FritzConnection
import xml.etree.ElementTree as ET
from library.Configuration import Configuration


class Fritzbox:
    # Definition of call's type value:
    # src: https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/x_contactSCPD.pdf
    # 1 incoming Call answered by phone or answering machine.
    # 2 missed Incoming call was not answered by internal phone or answering machine.
    # 3 outgoing Finished call to external number.
    # 9 active incoming Phone or answering machine has answered the incoming call and the call isn't over yet.
    # 10 rejected incoming The incoming call was refused e.g. by call barring.
    # 11 active outgoing Call to external number isn't over yet.
    CALL_TYPES = {
        1: "CALL_ANSWERED",
        2: "CALL_MISSED",
        3: "CALL_OUTGOING_FINISHED",
        9: "CALL_INCOMING_ACTIVE",
        10: "CALL_REFUSED",
        11: "CALL_OUTGOING_ACTIVE",
    }

    def __init__(self):
        self.config = Configuration()
        self.ip = self.config.fritz_api_ip() or "192.168.178.1"
        self.user = self.config.fritz_api_user() or ""
        self.password = self.config.fritz_api_pass() or ""

    def _get_connection(self):
        """Create a fresh FritzConnection instance"""
        return FritzConnection(address=self.ip, user=self.user, password=self.password)

    def get_call_history(self, limit=None):
        """Get call history from Fritzbox"""
        try:
            connection = self._get_connection()

            # Get URL to the call list with session id
            state = connection.call_action("X_AVM-DE_OnTel", "GetCallList")
            calllist_url = state.get("NewCallListURL")

            if not calllist_url:
                print("Could not get call list URL")
                return []

            # Parse xml content
            xml_content = requests.get(calllist_url).content
            root = ET.ElementTree(ET.fromstring(xml_content)).getroot()

            # Extract call data
            calls = []
            # Convert root to list to handle indexing
            if root is not None:
                root_list = list(root)
                # Loop over calls, skipping the first timestamp element
                start_idx = 1
                end_idx = (limit + 1) if limit else len(root_list)

                for call in root_list[start_idx:end_idx]:
                    call_data = self._extract_call_data(call)
                    if call_data and self._is_incoming_call(call_data):
                        calls.append(call_data)

            return calls

        except Exception as e:
            print(f"Error getting call history: {e}")
            return []

    def _extract_call_data(self, call_element):
        """Extract call data from XML element"""
        try:
            # XML structure based on test.py example:
            # [0] Id, [1] Type, [2] Caller, [3] Called, [4] CalledNumber,
            # [5] Name, [6] Numbertype, [7] Device, [8] Port, [9] Date, [10] Duration

            call_id = self._get_element_text(call_element, 0)
            call_type = self._get_element_text(call_element, 1)
            caller = self._get_element_text(call_element, 2)
            called = self._get_element_text(call_element, 3)
            called_number = self._get_element_text(call_element, 4)
            name = self._get_element_text(call_element, 5)
            number_type = self._get_element_text(call_element, 6)
            device = self._get_element_text(call_element, 7)
            port = self._get_element_text(call_element, 8)
            date = self._get_element_text(call_element, 9)
            duration = self._get_element_text(call_element, 10)

            # Parse duration
            duration_hours = 0
            duration_minutes = 0
            if duration and ":" in duration:
                duration_parts = duration.split(":")
                if len(duration_parts) >= 2:
                    duration_hours = int(duration_parts[0])
                    duration_minutes = int(duration_parts[1])

            return {
                "id": int(call_id) if call_id else 0,
                "type": int(call_type) if call_type else 0,
                "type_name": self.CALL_TYPES.get(int(call_type), "UNKNOWN")
                if call_type
                else "UNKNOWN",
                "caller": caller or "",
                "called": called or "",
                "called_number": called_number or "",
                "name": name or "",
                "number_type": number_type or "",
                "device": device or "",
                "port": int(port) if port else -1,
                "date": date or "",
                "duration": duration or "",
                "duration_hours": duration_hours,
                "duration_minutes": duration_minutes,
            }

        except Exception as e:
            print(f"Error extracting call data: {e}")
            return None

    def _get_element_text(self, parent, index):
        """Get text from element at specific index"""
        try:
            if len(parent) > index and parent[index].text:
                return parent[index].text.strip()
        except:
            pass
        return None

    def _is_incoming_call(self, call_data):
        """Check if call is incoming (types 1, 2, 9)"""
        call_type = call_data.get("type", 0)
        return call_type in [1, 2, 9]  # Incoming calls

    def get_call_history_formatted(self, limit=5):
        """Get formatted call history"""
        calls = self.get_call_history(limit)

        formatted_calls = []
        for call in calls:
            formatted = (
                f"Call - State: {call['type_name']}; "
                f"Called: {call['caller']}; "
                f"Date: {call['date']}; "
                f"Duration: {call['duration_hours']}h {call['duration_minutes']}min"
            )
            formatted_calls.append(formatted)

        return formatted_calls

    @staticmethod
    def telefonbuch_reverse_lookup(phonenumber):
        """Reverse phone number lookup using dastelefonbuch.de"""
        try:
            import urllib.request
            import urllib.parse
            import urllib.error
            import html
            import re

            # Clean phone number - remove spaces, dashes, etc.
            clean_number = re.sub(r"[\s\-\(\)]", "", phonenumber)

            # Use the search endpoint with form data
            search_url = "https://www.dastelefonbuch.de/Rueckwaerts-Suche"

            # Prepare form data
            form_data = urllib.parse.urlencode(
                {"phone": clean_number, "stype": "RBP", "mode": "search"}
            ).encode("utf-8")

            # Create request with proper headers
            req = urllib.request.Request(
                search_url,
                data=form_data,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
            )

            # Make request
            with urllib.request.urlopen(req, timeout=15) as response:
                html_content = response.read().decode("utf-8")

                # Look for name in multiple possible patterns
                name_patterns = [
                    # Pattern 1: Name in result entry
                    r'<div[^>]*class="name"[^>]*>([^<]+)</div>',
                    # Pattern 2: Name in h2 or h3 tags
                    r'<h[23][^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</h[23]>',
                    # Pattern 3: Name in data-name attribute
                    r'data-name="([^"]+)"',
                    # Pattern 4: Name in contact info section
                    r'<div[^>]*class="contact[^"]*"[^>]*>.*?<span[^>]*class="name"[^>]*>([^<]+)</span>',
                    # Pattern 5: General name extraction from result items
                    r'<div[^>]*class="result[^"]*"[^>]*>.*?([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+).*?</div>',
                    # Pattern 6: Look for names in result list items
                    r'<li[^>]*class="result[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>',
                    # Pattern 7: Look for names in address entries
                    r'<div[^>]*class="address[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>',
                ]

                for pattern in name_patterns:
                    try:
                        matches = re.findall(
                            pattern, html_content, re.IGNORECASE | re.DOTALL
                        )
                        if matches:
                            # Take the first match and clean it
                            name = html.unescape(matches[0].strip())
                            # Remove any remaining HTML tags
                            name = re.sub(r"<[^>]+>", "", name)
                            # Limit length and clean up
                            name = name[:50].strip()
                            print(name)
                            if (
                                name and len(name) > 2
                            ):  # Ensure we have a meaningful name
                                return name
                    except re.error:
                        # Skip patterns that cause encoding errors
                        continue

                # If no name found, try to extract from title or meta tags
                title_match = re.search(
                    r"<title>([^<]+)</title>", html_content, re.IGNORECASE
                )
                if title_match:
                    title = title_match.group(1)
                    if len(title) > 5 and "Telefonbuch" not in title:
                        print(title)
                        return html.unescape(title.strip())[:30]

                return None

        except urllib.error.HTTPError as http_err:
            if http_err.code == 404:
                return None  # Number not found
            elif http_err.code == 429:
                return None  # Rate limited
            else:
                return None
        except Exception as e:
            # Log error for debugging but don't crash
            print(f"Reverse lookup error: {e}")
            return None
