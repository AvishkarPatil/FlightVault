import mariadb
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class TemporalEngine:
    
    def __init__(self, config: Dict):
        self.config = config
        self.conn = mariadb.connect(**config)
        self.cursor = self.conn.cursor(dictionary=True)
        
        self.tables = {
            'airports': 'airport_id',
            'airlines': 'airline_id',
            'routes': 'route_id'
        }
    
    def query_as_of(self, table: str, timestamp: datetime, filters: Optional[Dict] = None) -> List[Dict]:
        query = f"SELECT * FROM {table} FOR SYSTEM_TIME AS OF '{timestamp.strftime('%Y-%m-%d %H:%M:%S')}'"
        
        if filters:
            where_clauses = [f"{key} = %s" for key in filters.keys()]
            query += " WHERE " + " AND ".join(where_clauses)
            self.cursor.execute(query, list(filters.values()))
        else:
            self.cursor.execute(query)
        
        return self.cursor.fetchall()
    
    def query_current(self, table: str, filters: Optional[Dict] = None) -> List[Dict]:
        query = f"SELECT * FROM {table}"
        
        if filters:
            where_clauses = [f"{key} = %s" for key in filters.keys()]
            query += " WHERE " + " AND ".join(where_clauses)
            self.cursor.execute(query, list(filters.values()))
        else:
            self.cursor.execute(query)
        
        return self.cursor.fetchall()
    
    def query_between(self, table: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        query = f"""
            SELECT *, ROW_START, ROW_END 
            FROM {table} 
            FOR SYSTEM_TIME BETWEEN '{start_time.strftime('%Y-%m-%d %H:%M:%S')}' 
            AND '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_audit_trail(self, table: str, limit: int = 1000) -> List[Dict]:
        query = f"""
            SELECT *, 
                   ROW_START as changed_at,
                   ROW_END as valid_until,
                   CASE 
                       WHEN ROW_END = TIMESTAMP'2038-01-19 03:14:07.999999' 
                       THEN 'CURRENT'
                       ELSE 'HISTORICAL'
                   END as status
            FROM {table} 
            FOR SYSTEM_TIME ALL
            ORDER BY ROW_START DESC 
            LIMIT {limit}
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def calculate_diff(self, before_data: List[Dict], after_data: List[Dict], table: str) -> Dict:
        pk = self.tables[table]
        before_dict = {row[pk]: row for row in before_data}
        after_dict = {row[pk]: row for row in after_data}
        
        added = [row for key, row in after_dict.items() if key not in before_dict]
        deleted = [row for key, row in before_dict.items() if key not in after_dict]
        
        # Find modified records
        modified = []
        for key in set(before_dict.keys()) & set(after_dict.keys()):
            before_row = before_dict[key]
            after_row = after_dict[key]
            
            if self._rows_different(before_row, after_row):
                modified.append({
                    'before': before_row,
                    'after': after_row,
                    'changes': self._get_field_changes(before_row, after_row)
                })
        
        return {
            'added': added,
            'deleted': deleted,
            'modified': modified,
            'summary': {
                'total_added': len(added),
                'total_deleted': len(deleted),
                'total_modified': len(modified)
            }
        }
    
    def restore_records(self, table: str, records: List[Dict]) -> Dict:
        restored_count = 0
        errors = []
        
        try:
            self.conn.begin()
            
            for record in records:
                clean_record = {k: v for k, v in record.items() 
                              if k not in ['ROW_START', 'ROW_END', 'changed_at', 'valid_until', 'status']}
                
                columns = ', '.join(clean_record.keys())
                placeholders = ', '.join(['%s' for _ in clean_record])
                
                # Use INSERT ... ON DUPLICATE KEY UPDATE to preserve history
                update_clause = ', '.join([f"{col} = VALUES({col})" for col in clean_record.keys() if col != self.tables[table]])
                if update_clause:
                    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"
                else:
                    query = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
                self.cursor.execute(query, list(clean_record.values()))
                restored_count += 1
            
            self.conn.commit()
            
            return {
                'success': True,
                'restored_count': restored_count,
                'errors': errors
            }
            
        except Exception as e:
            self.conn.rollback()
            return {
                'success': False,
                'restored_count': 0,
                'errors': [str(e)]
            }
    
    def _rows_different(self, row1: Dict, row2: Dict) -> bool:
        ignore_keys = {'ROW_START', 'ROW_END', 'changed_at', 'valid_until', 'status'}
        
        for key in row1:
            if key not in ignore_keys:
                if row1.get(key) != row2.get(key):
                    return True
        return False
    
    def _get_field_changes(self, before_row: Dict, after_row: Dict) -> List[Dict]:
        changes = []
        ignore_keys = {'ROW_START', 'ROW_END', 'changed_at', 'valid_until', 'status'}
        
        for key in before_row:
            if key not in ignore_keys:
                before_val = before_row.get(key)
                after_val = after_row.get(key)
                
                if before_val != after_val:
                    changes.append({
                        'field': key,
                        'before': before_val,
                        'after': after_val
                    })
        
        return changes
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def create_engine() -> TemporalEngine:
    from config import DATABASE_CONFIG
    return TemporalEngine(DATABASE_CONFIG)