"""
Data export system
Supports CSV and JSON export
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import config
from logger import monitor_logger


class DataExporter:
    """Export data to various formats"""
    
    def __init__(self, export_dir: Path = None):
        self.export_dir = export_dir or config.EXPORT_DIR
        config.ensure_directories()
    
    def _generate_filename(self, extension: str) -> Path:
        """Generate unique filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.export_dir / f"export_{timestamp}.{extension}"
    
    async def export_to_csv(
        self, 
        data: List[Dict[str, Any]], 
        filename: Path = None
    ) -> Optional[Path]:
        """Export to CSV"""
        if not data:
            monitor_logger.warning("No data to export")
            return None
        
        filepath = filename or self._generate_filename("csv")
        
        try:
            # Define columns
            fieldnames = [
                'id', 'message_id', 'channel_id', 'channel_username',
                'keyword_matched', 'message_text', 'message_link',
                'detected_at', 'notification_sent'
            ]
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)
            
            monitor_logger.info(f"Exported {len(data)} records to {filepath}")
            return filepath
            
        except Exception as e:
            monitor_logger.error(f"Error exporting CSV: {e}")
            return None
    
    async def export_to_json(
        self, 
        data: List[Dict[str, Any]], 
        filename: Path = None,
        pretty: bool = True
    ) -> Optional[Path]:
        """Export to JSON"""
        if not data:
            monitor_logger.warning("No data to export")
            return None
        
        filepath = filename or self._generate_filename("json")
        
        try:
            # Convert datetime to string
            serializable_data = []
            for item in data:
                clean_item = {}
                for key, value in item.items():
                    if isinstance(value, datetime):
                        clean_item[key] = value.isoformat()
                    else:
                        clean_item[key] = value
                serializable_data.append(clean_item)
            
            export_obj = {
                "exported_at": datetime.now().isoformat(),
                "total_records": len(serializable_data),
                "data": serializable_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(export_obj, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(export_obj, f, ensure_ascii=False)
            
            monitor_logger.info(f"Exported {len(data)} records to {filepath}")
            return filepath
            
        except Exception as e:
            monitor_logger.error(f"Error exporting JSON: {e}")
            return None
    
    async def export_stats_report(self, stats: Dict[str, Any]) -> Optional[Path]:
        """Export statistics report"""
        filepath = self._generate_filename("txt")
        
        try:
            report = f"""
╔══════════════════════════════════════════════════════════════╗
║           Channel Monitoring Statistics Report               ║
║              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📊 General Statistics:                                      ║
║  ━━━━━━━━━━━━━━━━━━━━                                        ║
║  • Total Detected Messages: {stats['total_messages']:>10}                 ║
║  • Today's Messages: {stats['today_messages']:>10}                              ║
║                                                              ║
║  🏆 Top Matching Keywords:                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━                                      ║
"""
            for i, kw in enumerate(stats.get('top_keywords', [])[:10], 1):
                report += f"║  {i:>2}. {kw['keyword_matched']:<20} - {kw['count']:>5} times    ║\n"
            
            report += """║                                                              ║
║  📢 Most Active Channels:                                    ║
║  ━━━━━━━━━━━━━━━━━━━━━━                                       ║
"""
            for i, ch in enumerate(stats.get('top_channels', [])[:10], 1):
                report += f"║  {i:>2}. @{ch['channel_username']:<18} - {ch['count']:>5} messages║\n"
            
            report += """║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            monitor_logger.info(f"Report exported to {filepath}")
            return filepath
            
        except Exception as e:
            monitor_logger.error(f"Error exporting report: {e}")
            return None


# Pandas Export (optional - for advanced export)
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class AdvancedExporter(DataExporter):
    """Advanced export using Pandas"""
    
    def __init__(self, export_dir: Path = None):
        super().__init__(export_dir)
        if not HAS_PANDAS:
            monitor_logger.warning("Pandas not installed - some export features will not work")
    
    async def export_to_excel(
        self, 
        data: List[Dict[str, Any]], 
        filename: Path = None
    ) -> Optional[Path]:
        """Export to Excel"""
        if not HAS_PANDAS:
            monitor_logger.error("Pandas required for Excel export")
            return None
        
        if not data:
            return None
        
        filepath = filename or self._generate_filename("xlsx")
        
        try:
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            monitor_logger.info(f"Exported {len(data)} records to {filepath}")
            return filepath
            
        except Exception as e:
            monitor_logger.error(f"Error exporting Excel: {e}")
            return None
    
    async def export_filtered(
        self,
        data: List[Dict[str, Any]],
        format: str = "csv",
        channel_filter: str = None,
        keyword_filter: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> Optional[Path]:
        """Filtered export"""
        if not HAS_PANDAS:
            # Use basic export
            filtered = data
            if channel_filter:
                filtered = [d for d in filtered if d.get('channel_username') == channel_filter]
            if keyword_filter:
                filtered = [d for d in filtered if d.get('keyword_matched') == keyword_filter]
            
            if format == "json":
                return await self.export_to_json(filtered)
            return await self.export_to_csv(filtered)
        
        df = pd.DataFrame(data)
        
        if channel_filter:
            df = df[df['channel_username'] == channel_filter]
        if keyword_filter:
            df = df[df['keyword_matched'] == keyword_filter]
        if date_from:
            df = df[pd.to_datetime(df['detected_at']) >= date_from]
        if date_to:
            df = df[pd.to_datetime(df['detected_at']) <= date_to]
        
        filtered_data = df.to_dict('records')
        
        if format == "json":
            return await self.export_to_json(filtered_data)
        elif format == "excel":
            return await self.export_to_excel(filtered_data)
        return await self.export_to_csv(filtered_data)
