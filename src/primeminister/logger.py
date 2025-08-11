import json
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class PrimeMinisterLogger:
    """JSON-based logger with monthly rotation for PrimeMinister sessions."""

    def __init__(self):
        self.is_linux = platform.system().lower() == 'linux'
        self.setup_logging_directory()

    def setup_logging_directory(self) -> None:
        """Setup logging directory based on platform."""
        if self.is_linux:
            self.log_dir = Path('/var/log/primeminister')
        else:
            self.log_dir = Path('./logs')

        # Create directory if it doesn't exist
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to local logs directory if we can't write to /var/log
            self.log_dir = Path('./logs')
            self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_current_log_file(self) -> Path:
        """Get the current month's log file path."""
        now = datetime.now()
        filename = f"{now.year}-{now.month:02d}.json"
        return self.log_dir / filename

    def load_existing_logs(self) -> List[Dict[str, Any]]:
        """Load existing logs from current month's file."""
        log_file = self.get_current_log_file()

        if not log_file.exists():
            return []

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_logs(self, logs: List[Dict[str, Any]]) -> None:
        """Save logs to current month's file."""
        log_file = self.get_current_log_file()

        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False, default=str)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to save logs to {log_file}: {e}")

    def log_session(self,
                   prompt: str,
                   council_responses: List[Dict[str, Any]],
                   votes: Dict[str, List[str]],
                   final_result: str,
                   metadata: Dict[str, Any] = None,
                   first_round_opinions: List[Dict[str, Any]] = None,
                   second_round_responses: List[Dict[str, Any]] = None) -> None:
        """Log a complete PrimeMinister session."""

        # Build council members with opinion arrays nested on each entry
        council_members = []
        for response in council_responses:
            member_entry = {
                "personality": response.get("personality", "Unknown"),
                "model": response.get("model", "Unknown"),
                "entry": response.get("response", ""),
                "is_voter": response.get("is_voter", True),
                "is_silent": response.get("is_silent", False),
                "uuid": response.get("uuid")
            }

            # Add first round opinions received about this member's response
            if first_round_opinions:
                opinions_on_this_response = [
                    opinion for opinion in first_round_opinions
                    if opinion.get("target_response_uuid") == response.get("uuid")
                ]

                if opinions_on_this_response:
                    member_entry["opinions_received"] = opinions_on_this_response

            # Add this member's second round response (if they gave one)
            if second_round_responses:
                member_second_round = next(
                    (sr for sr in second_round_responses
                     if sr.get("original_response_uuid") == response.get("uuid")),
                    None
                )

                if member_second_round:
                    member_entry["second_round_response"] = member_second_round

            council_members.append(member_entry)

        # Build session entry
        session_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "council_members": council_members,
            "votes": votes,
            "final_result": final_result,
            "metadata": metadata or {}
        }

        # Load existing logs
        logs = self.load_existing_logs()

        # Add new session
        logs.append(session_entry)

        # Save updated logs
        self.save_logs(logs)

    def get_session_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get session history, optionally limited to recent entries."""
        logs = self.load_existing_logs()

        if limit:
            return logs[-limit:]
        return logs

    def setup_standard_logging(self) -> logging.Logger:
        """Setup standard Python logging for debugging and errors."""
        logger = logging.getLogger('primeminister')

        if not logger.handlers:
            # Create handler for standard logs
            log_file = self.log_dir / 'primeminister.log'
            handler = logging.FileHandler(log_file)

            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)

            # Add handler to logger
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger