"""
Diff Analyzer - Compare timestamps and detect changes
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional
from core.temporal_engine import TemporalEngine

class DiffAnalyzer:
    """Analyze differences between timestamps"""
    
    def __init__(self, engine: TemporalEngine):
        self.engine = engine
    
    def compare_timestamps(self, table: str, timestamp1: datetime, 
                          timestamp2: Optional[datetime] = None) -> Dict:
        """Compare data between two timestamps"""
        
        if timestamp2 is None:
            timestamp2 = datetime.now()
        
        # Get data at both timestamps
        data1 = self.engine.query_as_of(table, timestamp1)
        data2 = self.engine.query_as_of(table, timestamp2)
        
        # Calculate differences
        added, removed, modified = self._calculate_diff(data1, data2, table)
        
        return {
            'timestamp1': timestamp1,
            'timestamp2': timestamp2,
            'count_before': len(data1),
            'count_after': len(data2),
            'changes': {
                'added': added,
                'removed': removed,
                'modified': modified
            },
            'summary': {
                'total_changes': len(added) + len(removed) + len(modified),
                'net_change': len(data2) - len(data1)
            }
        }
    
    def _calculate_diff(self, data1: List[Dict], data2: List[Dict], table: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Calculate added, removed, and modified records"""
        
        # Get primary key field
        pk_field = self._get_primary_key(table)
        
        # Create lookup dictionaries
        dict1 = {record[pk_field]: record for record in data1}
        dict2 = {record[pk_field]: record for record in data2}
        
        # Find differences
        added = [record for pk, record in dict2.items() if pk not in dict1]
        removed = [record for pk, record in dict1.items() if pk not in dict2]
        
        # Find modified records
        modified = []
        for pk in dict1:
            if pk in dict2 and dict1[pk] != dict2[pk]:
                modified.append({
                    'before': dict1[pk],
                    'after': dict2[pk],
                    'changes': self._field_changes(dict1[pk], dict2[pk])
                })
        
        return added, removed, modified
    
    def _get_primary_key(self, table: str) -> str:
        """Get primary key field for table"""
        pk_map = {
            'airports': 'airport_id',
            'airlines': 'airline_id', 
            'routes': 'route_id'
        }
        return pk_map.get(table, 'id')
    
    def _field_changes(self, before: Dict, after: Dict) -> Dict:
        """Identify which fields changed"""
        changes = {}
        for field in before:
            if field in after and before[field] != after[field]:
                changes[field] = {
                    'before': before[field],
                    'after': after[field]
                }
        return changes