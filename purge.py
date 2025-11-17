#!/usr/bin/env python3
"""
File Purge Script - Automatically deletes old files and empty directories
Sends notifications to Discord webhook
"""

import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Handle Discord webhook notifications"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)

    def send_notification(self, title: str, description: str, color: int = 0x00ff00):
        """Send embedded message to Discord"""
        if not self.enabled:
            logger.warning(
                "Discord webhook not configured, skipping notification")
            return

        embed = {
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "File Purge Script"}
            }]
        }

        try:
            response = requests.post(self.webhook_url, json=embed, timeout=10)
            response.raise_for_status()
            logger.info(f"Discord notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")


class FilePurger:
    """Main file purge functionality"""

    def __init__(
        self,
        target_dir: str,
        max_age_days: int,
        check_interval_seconds: int,
        discord_notifier: DiscordNotifier,
        dry_run: bool = False
    ):
        self.target_dir = Path(target_dir)
        self.max_age_days = max_age_days
        self.check_interval_seconds = check_interval_seconds
        self.discord_notifier = discord_notifier
        self.dry_run = dry_run

        if not self.target_dir.exists():
            raise ValueError(f"Target directory does not exist: {target_dir}")

    def get_file_age_days(self, file_path: Path) -> float:
        """Calculate file age in days based on modification time"""
        mtime = file_path.stat().st_mtime
        age_seconds = time.time() - mtime
        return age_seconds / 86400  # Convert to days

    def find_old_files(self) -> List[Path]:
        """Find all files older than max_age_days"""
        old_files = []

        try:
            for item in self.target_dir.rglob('*'):
                if item.is_file():
                    age_days = self.get_file_age_days(item)
                    if age_days > self.max_age_days:
                        old_files.append(item)
                        logger.debug(
                            f"Found old file: {item} (age: {age_days:.1f} days)")
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")

        return old_files

    def delete_file(self, file_path: Path) -> bool:
        """Delete a single file"""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would delete file: {file_path}")
                return True

            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def remove_empty_directories(self) -> List[Path]:
        """Remove empty directories recursively, bottom-up"""
        removed_dirs = []

        try:
            # Get all directories, sorted by depth (deepest first)
            all_dirs = sorted(
                [d for d in self.target_dir.rglob('*') if d.is_dir()],
                key=lambda x: len(x.parts),
                reverse=True
            )

            for directory in all_dirs:
                if directory == self.target_dir:
                    continue  # Don't delete the root target directory

                try:
                    # Check if directory is empty
                    if not any(directory.iterdir()):
                        if self.dry_run:
                            logger.info(
                                f"[DRY RUN] Would delete empty directory: {directory}")
                            removed_dirs.append(directory)
                        else:
                            directory.rmdir()
                            logger.info(
                                f"Deleted empty directory: {directory}")
                            removed_dirs.append(directory)
                except Exception as e:
                    logger.error(
                        f"Failed to check/delete directory {directory}: {e}")

        except Exception as e:
            logger.error(f"Error during empty directory removal: {e}")

        return removed_dirs

    def format_file_path(self, file_path: Path) -> str:
        """Format file path relative to target directory"""
        try:
            return str(file_path.relative_to(self.target_dir))
        except ValueError:
            return str(file_path)

    def format_file_size(self, file_path: Path) -> str:
        """Format file size in human-readable format"""
        try:
            size = file_path.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "?"

    def run_purge(self) -> Dict:
        """Execute one purge cycle"""
        logger.info("=" * 60)
        logger.info("Starting purge cycle")
        logger.info(f"Target directory: {self.target_dir}")
        logger.info(f"Max file age: {self.max_age_days} days")
        logger.info(f"Dry run mode: {self.dry_run}")
        logger.info("=" * 60)

        # Find and delete old files
        old_files = self.find_old_files()
        deleted_files = []
        deleted_files_info = []  # Store file info before deletion
        failed_files = []

        for file_path in old_files:
            # Collect file info BEFORE deletion
            try:
                file_info = {
                    'path': file_path,
                    'relative_path': self.format_file_path(file_path),
                    'size': self.format_file_size(file_path),
                    'age_days': self.get_file_age_days(file_path)
                }
            except Exception as e:
                logger.warning(f"Could not get info for {file_path}: {e}")
                file_info = {
                    'path': file_path,
                    'relative_path': self.format_file_path(file_path),
                    'size': '?',
                    'age_days': 0
                }

            # Now delete the file
            if self.delete_file(file_path):
                deleted_files.append(file_path)
                deleted_files_info.append(file_info)
            else:
                failed_files.append(file_path)

        # Remove empty directories
        removed_dirs = self.remove_empty_directories()

        # Prepare summary
        results = {
            'deleted_files': deleted_files,
            'deleted_files_info': deleted_files_info,  # Include pre-deletion info
            'failed_files': failed_files,
            'removed_directories': removed_dirs,
            'timestamp': datetime.now()
        }

        # Log summary
        logger.info("-" * 60)
        logger.info("Purge cycle completed:")
        logger.info(f"  Files deleted: {len(deleted_files)}")
        logger.info(f"  Files failed: {len(failed_files)}")
        logger.info(f"  Directories removed: {len(removed_dirs)}")
        logger.info("=" * 60)

        # Send Discord notification
        if len(deleted_files) > 0 or len(removed_dirs) > 0:
            self._send_purge_notification(results)
        else:
            self._send_no_action_notification()

        return results

    def _send_purge_notification(self, results: Dict):
        """Send detailed Discord notification about purge results"""
        deleted_files_info = results.get('deleted_files_info', [])
        removed_dirs = results['removed_directories']
        failed_files = results['failed_files']

        # Build message
        message_parts = []

        # Header with summary
        header = f"🗑️ **Gelöschte Dateien:** {len(deleted_files_info)}"
        if len(removed_dirs) > 0:
            header += f"\n📂 **Leere Verzeichnisse entfernt:** {len(removed_dirs)}"
        if len(failed_files) > 0:
            header += f"\n⚠️ **Fehler:** {len(failed_files)}"

        message_parts.append(header)

        # List deleted files (limit to avoid Discord message size limits)
        if deleted_files_info:
            message_parts.append("\n**Gelöschte Dateien:**")
            max_files_to_show = 15

            for i, file_info in enumerate(deleted_files_info[:max_files_to_show]):
                rel_path = file_info['relative_path']
                size = file_info['size']
                age = file_info['age_days']
                message_parts.append(
                    f"• `{rel_path}` ({size}, {age:.0f} Tage alt)")

            if len(deleted_files_info) > max_files_to_show:
                remaining = len(deleted_files_info) - max_files_to_show
                message_parts.append(f"... und {remaining} weitere Datei(en)")

        # List removed directories
        if removed_dirs:
            message_parts.append("\n**Entfernte Verzeichnisse:**")
            max_dirs_to_show = 10

            for i, dir_path in enumerate(removed_dirs[:max_dirs_to_show]):
                rel_path = self.format_file_path(dir_path)
                message_parts.append(f"• `{rel_path}/`")

            if len(removed_dirs) > max_dirs_to_show:
                remaining = len(removed_dirs) - max_dirs_to_show
                message_parts.append(
                    f"... und {remaining} weitere Verzeichnis(se)")

        # List failed files if any
        if failed_files:
            message_parts.append("\n**Fehler beim Löschen:**")
            for file_path in failed_files[:5]:
                rel_path = self.format_file_path(file_path)
                message_parts.append(f"• `{rel_path}`")

        message = "\n".join(message_parts)

        # Add dry run prefix if applicable
        if self.dry_run:
            message = "**[DRY RUN - Keine Dateien wurden tatsächlich gelöscht]**\n\n" + message

        # Determine color
        color = 0x00ff00 if len(failed_files) == 0 else 0xffa500

        # Send notification
        title = "File Purge Report" if not self.dry_run else "File Purge Report (DRY RUN)"
        self.discord_notifier.send_notification(title, message, color)

    def _send_no_action_notification(self):
        """Send notification when no files were deleted"""
        next_check = datetime.now() + timedelta(seconds=self.check_interval_seconds)
        next_check_str = next_check.strftime("%d.%m.%Y %H:%M:%S")

        message = (
            f"✅ **Keine Dateien zum Löschen gefunden**\n\n"
            f"🔍 Alle Dateien sind neuer als {self.max_age_days} Tage\n"
            f"⏰ Nächster Check: {next_check_str}"
        )

        self.discord_notifier.send_notification(
            "File Purge - Keine Aktion erforderlich",
            message,
            0x808080  # Gray color
        )

    def run_continuous(self):
        """Run purge cycles continuously based on check interval"""
        logger.info(
            f"Starting continuous purge mode (interval: {self.check_interval_seconds}s)")

        # Send startup notification
        self.discord_notifier.send_notification(
            "File Purge Script gestartet",
            f"⏱️ **Intervall:** {self.check_interval_seconds}s\n"
            f"📅 **Max. Alter:** {self.max_age_days} Tage\n"
            f"🔍 **Dry Run:** {'Ja' if self.dry_run else 'Nein'}",
            0x0099ff
        )

        try:
            while True:
                self.run_purge()
                logger.info(
                    f"Waiting {self.check_interval_seconds} seconds until next check...")
                time.sleep(self.check_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Purge script stopped by user")
            self.discord_notifier.send_notification(
                "File Purge Script beendet",
                "Script wurde gestoppt",
                0xff0000
            )
        except Exception as e:
            logger.error(f"Fatal error in continuous mode: {e}")
            self.discord_notifier.send_notification(
                "File Purge Script Fehler",
                f"⚠️ Kritischer Fehler: {str(e)}",
                0xff0000
            )
            raise


def main():
    """Main entry point"""
    # Load configuration from environment variables
    TARGET_DIR = os.getenv('PURGE_TARGET_DIR', '/data')
    MAX_AGE_DAYS = int(os.getenv('PURGE_MAX_AGE_DAYS', '30'))
    CHECK_INTERVAL = int(
        os.getenv('PURGE_CHECK_INTERVAL', '3600'))  # 1 hour default
    DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL', '')
    DRY_RUN = os.getenv('PURGE_DRY_RUN', 'false').lower() in (
        'true', '1', 'yes')

    # Initialize Discord notifier
    discord = DiscordNotifier(DISCORD_WEBHOOK)

    # Initialize and run purger
    try:
        purger = FilePurger(
            target_dir=TARGET_DIR,
            max_age_days=MAX_AGE_DAYS,
            check_interval_seconds=CHECK_INTERVAL,
            discord_notifier=discord,
            dry_run=DRY_RUN
        )
        purger.run_continuous()
    except Exception as e:
        logger.error(f"Failed to start purge script: {e}")
        discord.send_notification(
            "File Purge Script Fehler",
            f"⚠️ Konnte nicht starten: {str(e)}",
            0xff0000
        )
        raise


if __name__ == '__main__':
    main()
