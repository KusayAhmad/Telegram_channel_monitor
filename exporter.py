"""
نظام تصدير البيانات
يدعم تصدير CSV و JSON
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import config
from logger import monitor_logger


class DataExporter:
    """تصدير البيانات إلى صيغ مختلفة"""
    
    def __init__(self, export_dir: Path = None):
        self.export_dir = export_dir or config.EXPORT_DIR
        config.ensure_directories()
    
    def _generate_filename(self, extension: str) -> Path:
        """إنشاء اسم ملف فريد"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.export_dir / f"export_{timestamp}.{extension}"
    
    async def export_to_csv(
        self, 
        data: List[Dict[str, Any]], 
        filename: Path = None
    ) -> Optional[Path]:
        """تصدير إلى CSV"""
        if not data:
            monitor_logger.warning("لا توجد بيانات للتصدير")
            return None
        
        filepath = filename or self._generate_filename("csv")
        
        try:
            # تحديد الأعمدة
            fieldnames = [
                'id', 'message_id', 'channel_id', 'channel_username',
                'keyword_matched', 'message_text', 'message_link',
                'detected_at', 'notification_sent'
            ]
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)
            
            monitor_logger.info(f"تم تصدير {len(data)} سجل إلى {filepath}")
            return filepath
            
        except Exception as e:
            monitor_logger.error(f"خطأ في تصدير CSV: {e}")
            return None
    
    async def export_to_json(
        self, 
        data: List[Dict[str, Any]], 
        filename: Path = None,
        pretty: bool = True
    ) -> Optional[Path]:
        """تصدير إلى JSON"""
        if not data:
            monitor_logger.warning("لا توجد بيانات للتصدير")
            return None
        
        filepath = filename or self._generate_filename("json")
        
        try:
            # تحويل datetime إلى string
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
            
            monitor_logger.info(f"تم تصدير {len(data)} سجل إلى {filepath}")
            return filepath
            
        except Exception as e:
            monitor_logger.error(f"خطأ في تصدير JSON: {e}")
            return None
    
    async def export_stats_report(self, stats: Dict[str, Any]) -> Optional[Path]:
        """تصدير تقرير الإحصائيات"""
        filepath = self._generate_filename("txt")
        
        try:
            report = f"""
╔══════════════════════════════════════════════════════════════╗
║              تقرير إحصائيات مراقبة القنوات                  ║
║              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📊 الإحصائيات العامة:                                      ║
║  ━━━━━━━━━━━━━━━━━━━━                                        ║
║  • إجمالي الرسائل المكتشفة: {stats['total_messages']:>10}                 ║
║  • رسائل اليوم: {stats['today_messages']:>10}                              ║
║                                                              ║
║  🏆 أكثر الكلمات تطابقاً:                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━                                      ║
"""
            for i, kw in enumerate(stats.get('top_keywords', [])[:10], 1):
                report += f"║  {i:>2}. {kw['keyword_matched']:<20} - {kw['count']:>5} مرة     ║\n"
            
            report += """║                                                              ║
║  📢 أكثر القنوات نشاطاً:                                    ║
║  ━━━━━━━━━━━━━━━━━━━━━━                                       ║
"""
            for i, ch in enumerate(stats.get('top_channels', [])[:10], 1):
                report += f"║  {i:>2}. @{ch['channel_username']:<18} - {ch['count']:>5} رسالة   ║\n"
            
            report += """║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            monitor_logger.info(f"تم تصدير التقرير إلى {filepath}")
            return filepath
            
        except Exception as e:
            monitor_logger.error(f"خطأ في تصدير التقرير: {e}")
            return None


# Pandas Export (اختياري - للتصدير المتقدم)
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class AdvancedExporter(DataExporter):
    """تصدير متقدم باستخدام Pandas"""
    
    def __init__(self, export_dir: Path = None):
        super().__init__(export_dir)
        if not HAS_PANDAS:
            monitor_logger.warning("Pandas غير مثبت - بعض ميزات التصدير لن تعمل")
    
    async def export_to_excel(
        self, 
        data: List[Dict[str, Any]], 
        filename: Path = None
    ) -> Optional[Path]:
        """تصدير إلى Excel"""
        if not HAS_PANDAS:
            monitor_logger.error("Pandas مطلوب للتصدير إلى Excel")
            return None
        
        if not data:
            return None
        
        filepath = filename or self._generate_filename("xlsx")
        
        try:
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            monitor_logger.info(f"تم تصدير {len(data)} سجل إلى {filepath}")
            return filepath
            
        except Exception as e:
            monitor_logger.error(f"خطأ في تصدير Excel: {e}")
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
        """تصدير مُفلتر"""
        if not HAS_PANDAS:
            # استخدم التصدير العادي
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
