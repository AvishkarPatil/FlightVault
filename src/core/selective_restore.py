"""
Selective Restore Engine - Surgical Recovery of Database Disasters
Enables granular restoration of only corrupted data while preserving legitimate changes
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from src.core.temporal_engine import TemporalEngine

class SelectiveRestoreEngine:
    """Engine for selective restoration of temporal data"""
    
    def __init__(self, engine: TemporalEngine):
        self.engine = engine
    
    def analyze_changes(self, table: str, restore_timestamp: datetime) -> Dict:
        """
        Component 1: Diff Analysis Engine
        Calculate comprehensive differences between historical and current states
        """
        
        print(f"🔍 Analyzing changes between {restore_timestamp.strftime('%H:%M:%S')} and current state...")
        
        # Get both states
        historical_data = self.engine.query_as_of(table, restore_timestamp)
        current_data = self.engine.query_current(table)
        
        # Build lookup dictionaries
        pk_field = self.engine.tables[table]
        historical_dict = {row[pk_field]: row for row in historical_data}
        current_dict = {row[pk_field]: row for row in current_data}
        
        # Calculate changes
        deleted_records = []  # In historical, not in current
        added_records = []    # In current, not in historical  
        modified_records = [] # In both but different
        
        # Find deleted records
        for record_id, historical_record in historical_dict.items():
            if record_id not in current_dict:
                # Get deletion timestamp from audit trail
                deletion_time = self._get_deletion_timestamp(table, record_id, restore_timestamp)
                deleted_records.append({
                    'id': record_id,
                    'historical_data': historical_record,
                    'deletion_timestamp': deletion_time
                })
        
        # Find added records
        for record_id, current_record in current_dict.items():
            if record_id not in historical_dict:
                # Get creation timestamp
                creation_time = self._get_creation_timestamp(table, record_id)
                added_records.append({
                    'id': record_id,
                    'current_data': current_record,
                    'creation_timestamp': creation_time
                })
        
        # Find modified records
        for record_id in set(historical_dict.keys()) & set(current_dict.keys()):
            historical_record = historical_dict[record_id]
            current_record = current_dict[record_id]
            
            if self.engine._rows_different(historical_record, current_record):
                changes = self.engine._get_field_changes(historical_record, current_record)
                modification_time = self._get_modification_timestamp(table, record_id, restore_timestamp)
                
                modified_records.append({
                    'id': record_id,
                    'historical_data': historical_record,
                    'current_data': current_record,
                    'changed_fields': changes,
                    'modification_timestamp': modification_time
                })
        
        change_set = {
            'deleted_records': deleted_records,
            'added_records': added_records,
            'modified_records': modified_records,
            'summary': {
                'total_deleted': len(deleted_records),
                'total_added': len(added_records),
                'total_modified': len(modified_records),
                'total_changes': len(deleted_records) + len(added_records) + len(modified_records)
            }
        }
        
        print(f"   Found {change_set['summary']['total_changes']} total changes")
        print(f"   Deleted: {len(deleted_records)}, Added: {len(added_records)}, Modified: {len(modified_records)}")
        
        return change_set
    
    def classify_changes(self, change_set: Dict, rules: Optional[List[Dict]] = None) -> Dict:
        """
        Component 2: Change Classification System
        Categorize changes as 'legitimate' (keep) or 'corrupted' (restore)
        """
        
        print(f"🎯 Classifying changes...")
        
        classification = {
            'keep_records': [],      # Legitimate changes to preserve
            'restore_records': [],   # Corrupted data to restore
            'uncertain_records': []  # Require user decision
        }
        
        # Apply rules if provided
        if rules:
            classification = self._apply_rules(change_set, rules)
        else:
            # Use heuristic analysis
            classification = self._heuristic_analysis(change_set)
        
        print(f"   Keep: {len(classification['keep_records'])}")
        print(f"   Restore: {len(classification['restore_records'])}")
        print(f"   Uncertain: {len(classification['uncertain_records'])}")
        
        return classification
    
    def validate_dependencies(self, table: str, restore_list: List[Dict]) -> Dict:
        """
        Component 3: Dependency Validation Engine
        Ensure selective restoration maintains referential integrity
        """
        
        print(f"🔗 Validating dependencies...")
        
        validation_result = {
            'safe_to_restore': True,
            'foreign_key_issues': [],
            'cascade_impact': {},
            'warnings': [],
            'affected_tables': set()
        }
        
        # Check foreign key relationships
        if table == 'airports':
            validation_result = self._validate_airport_dependencies(restore_list)
        elif table == 'routes':
            validation_result = self._validate_route_dependencies(restore_list)
        
        print(f"   Safe to restore: {validation_result['safe_to_restore']}")
        print(f"   Affected tables: {len(validation_result['affected_tables'])}")
        
        return validation_result
    
    def execute_selective_restore(self, table: str, restore_list: List[Dict], 
                                 validation_result: Dict) -> Dict:
        """
        Component 4: Transactional Restore Executor
        Execute selective restoration with ACID guarantees
        """
        
        print(f"🚀 Executing selective restore...")
        
        if not validation_result['safe_to_restore']:
            return {
                'success': False,
                'error': 'Validation failed - restore aborted',
                'details': validation_result
            }
        
        execution_result = {
            'success': False,
            'records_processed': 0,
            'batches_completed': 0,
            'execution_time': 0,
            'errors': []
        }
        
        try:
            start_time = datetime.now()
            
            # Begin transaction
            self.engine.conn.begin()
            
            # Process in batches
            batch_size = 100
            total_records = len(restore_list)
            batches = [restore_list[i:i + batch_size] for i in range(0, total_records, batch_size)]
            
            for batch_num, batch in enumerate(batches, 1):
                print(f"   Processing batch {batch_num}/{len(batches)} ({len(batch)} records)")
                
                # Execute batch restore
                batch_result = self._execute_batch_restore(table, batch)
                
                if not batch_result['success']:
                    # Rollback on failure
                    self.engine.conn.rollback()
                    execution_result['errors'].extend(batch_result['errors'])
                    return execution_result
                
                execution_result['records_processed'] += batch_result['records_processed']
                execution_result['batches_completed'] += 1
                
                # Validate after each batch
                if not self._validate_batch_integrity(table, batch):
                    self.engine.conn.rollback()
                    execution_result['errors'].append(f"Integrity check failed after batch {batch_num}")
                    return execution_result
            
            # Final validation
            if self._final_validation_check(table, restore_list):
                self.engine.conn.commit()
                execution_result['success'] = True
                print(f"   ✅ Selective restore completed successfully")
            else:
                self.engine.conn.rollback()
                execution_result['errors'].append("Final validation failed")
            
            execution_result['execution_time'] = (datetime.now() - start_time).total_seconds()
            
        except Exception as e:
            self.engine.conn.rollback()
            execution_result['errors'].append(str(e))
        
        return execution_result
    
    def _get_deletion_timestamp(self, table: str, record_id: int, after_timestamp: datetime) -> Optional[datetime]:
        """Get when a record was deleted"""
        try:
            audit_trail = self.engine.get_audit_trail(table, limit=1000)
            pk_field = self.engine.tables[table]
            
            for entry in audit_trail:
                if (entry.get(pk_field) == record_id and 
                    entry['status'] == 'HISTORICAL' and
                    entry['changed_at'] > after_timestamp):
                    return entry['valid_until']
            
            return None
        except:
            return None
    
    def _get_creation_timestamp(self, table: str, record_id: int) -> Optional[datetime]:
        """Get when a record was created"""
        try:
            audit_trail = self.engine.get_audit_trail(table, limit=1000)
            pk_field = self.engine.tables[table]
            
            # Find earliest entry for this record
            record_entries = [entry for entry in audit_trail if entry.get(pk_field) == record_id]
            if record_entries:
                earliest = min(record_entries, key=lambda x: x['changed_at'])
                return earliest['changed_at']
            
            return None
        except:
            return None
    
    def _get_modification_timestamp(self, table: str, record_id: int, after_timestamp: datetime) -> Optional[datetime]:
        """Get when a record was last modified after given timestamp"""
        try:
            audit_trail = self.engine.get_audit_trail(table, limit=1000)
            pk_field = self.engine.tables[table]
            
            modifications = [
                entry for entry in audit_trail 
                if (entry.get(pk_field) == record_id and 
                    entry['changed_at'] > after_timestamp)
            ]
            
            if modifications:
                latest = max(modifications, key=lambda x: x['changed_at'])
                return latest['changed_at']
            
            return None
        except:
            return None
    
    def _apply_rules(self, change_set: Dict, rules: List[Dict]) -> Dict:
        """Apply user-defined rules for classification"""
        
        classification = {
            'keep_records': [],
            'restore_records': [],
            'uncertain_records': []
        }
        
        # Process each type of change
        all_changes = (
            [{'type': 'deleted', 'data': r} for r in change_set['deleted_records']] +
            [{'type': 'added', 'data': r} for r in change_set['added_records']] +
            [{'type': 'modified', 'data': r} for r in change_set['modified_records']]
        )
        
        for change in all_changes:
            matched_rule = False
            
            for rule in rules:
                if self._matches_rule(change, rule):
                    if rule['action'] == 'keep':
                        classification['keep_records'].append(change)
                    elif rule['action'] == 'restore':
                        classification['restore_records'].append(change)
                    matched_rule = True
                    break
            
            if not matched_rule:
                classification['uncertain_records'].append(change)
        
        return classification
    
    def _matches_rule(self, change: Dict, rule: Dict) -> bool:
        """Check if a change matches a classification rule"""
        
        # Simple rule matching - can be extended
        if 'change_type' in rule and change['type'] != rule['change_type']:
            return False
        
        if 'field_pattern' in rule:
            if change['type'] == 'modified':
                changed_fields = [cf['field'] for cf in change['data']['changed_fields']]
                if not any(rule['field_pattern'] in field for field in changed_fields):
                    return False
        
        if 'time_range' in rule:
            change_time = change['data'].get('creation_timestamp') or change['data'].get('modification_timestamp')
            if change_time:
                start_time, end_time = rule['time_range']
                if not (start_time <= change_time <= end_time):
                    return False
        
        return True
    
    def _heuristic_analysis(self, change_set: Dict) -> Dict:
        """Automatic heuristic-based classification"""
        
        classification = {
            'keep_records': [],
            'restore_records': [],
            'uncertain_records': []
        }
        
        # Heuristic 1: Recent additions are likely legitimate
        current_time = datetime.now()
        for added_record in change_set['added_records']:
            creation_time = added_record.get('creation_timestamp')
            if creation_time and (current_time - creation_time).total_seconds() < 3600:  # Last hour
                classification['keep_records'].append({'type': 'added', 'data': added_record})
            else:
                classification['uncertain_records'].append({'type': 'added', 'data': added_record})
        
        # Heuristic 2: Mass deletions are likely corrupted
        if len(change_set['deleted_records']) > 10:  # Mass deletion threshold
            for deleted_record in change_set['deleted_records']:
                classification['restore_records'].append({'type': 'deleted', 'data': deleted_record})
        else:
            for deleted_record in change_set['deleted_records']:
                classification['uncertain_records'].append({'type': 'deleted', 'data': deleted_record})
        
        # Heuristic 3: Modifications to critical fields are suspicious
        for modified_record in change_set['modified_records']:
            critical_fields_changed = any(
                change['field'] in ['name', 'iata_code', 'price'] 
                for change in modified_record['changed_fields']
            )
            
            if critical_fields_changed:
                classification['restore_records'].append({'type': 'modified', 'data': modified_record})
            else:
                classification['keep_records'].append({'type': 'modified', 'data': modified_record})
        
        return classification
    
    def _validate_airport_dependencies(self, restore_list: List[Dict]) -> Dict:
        """Validate dependencies for airport restoration"""
        
        validation = {
            'safe_to_restore': True,
            'foreign_key_issues': [],
            'cascade_impact': {},
            'warnings': [],
            'affected_tables': {'routes'}
        }
        
        # Check if restoring airports will break route references
        airport_ids = [item['data']['id'] for item in restore_list if item['type'] == 'deleted']
        
        if airport_ids:
            # Check current routes that reference these airports
            current_routes = self.engine.query_current('routes')
            affected_routes = [
                route for route in current_routes
                if (route.get('source_airport_id') in airport_ids or 
                    route.get('destination_airport_id') in airport_ids)
            ]
            
            if affected_routes:
                validation['cascade_impact']['routes'] = len(affected_routes)
                validation['warnings'].append(f"Restoring will affect {len(affected_routes)} existing routes")
        
        return validation
    
    def _validate_route_dependencies(self, restore_list: List[Dict]) -> Dict:
        """Validate dependencies for route restoration"""
        
        validation = {
            'safe_to_restore': True,
            'foreign_key_issues': [],
            'cascade_impact': {},
            'warnings': [],
            'affected_tables': {'airports', 'airlines'}
        }
        
        # Check if airports and airlines exist for restored routes
        route_records = [item['data'] for item in restore_list if item['type'] in ['deleted', 'modified']]
        
        for route_data in route_records:
            if 'historical_data' in route_data:
                route = route_data['historical_data']
                
                # Check if referenced airports exist
                source_id = route.get('source_airport_id')
                dest_id = route.get('destination_airport_id')
                
                if source_id or dest_id:
                    current_airports = self.engine.query_current('airports')
                    airport_ids = {apt['airport_id'] for apt in current_airports}
                    
                    if source_id and source_id not in airport_ids:
                        validation['foreign_key_issues'].append(f"Route references non-existent source airport {source_id}")
                        validation['safe_to_restore'] = False
                    
                    if dest_id and dest_id not in airport_ids:
                        validation['foreign_key_issues'].append(f"Route references non-existent destination airport {dest_id}")
                        validation['safe_to_restore'] = False
        
        return validation
    
    def _execute_batch_restore(self, table: str, batch: List[Dict]) -> Dict:
        """Execute restoration for a batch of records"""
        
        try:
            records_processed = 0
            
            for item in batch:
                change_type = item['type']
                change_data = item['data']
                
                if change_type == 'deleted':
                    # Restore deleted record
                    historical_data = change_data['historical_data']
                    clean_record = {k: v for k, v in historical_data.items() 
                                  if k not in ['ROW_START', 'ROW_END', 'changed_at', 'valid_until', 'status']}
                    
                    columns = ', '.join(clean_record.keys())
                    placeholders = ', '.join(['%s' for _ in clean_record])
                    query = f"REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
                    
                    self.engine.cursor.execute(query, list(clean_record.values()))
                    records_processed += 1
                
                elif change_type == 'modified':
                    # Restore to historical version
                    historical_data = change_data['historical_data']
                    clean_record = {k: v for k, v in historical_data.items() 
                                  if k not in ['ROW_START', 'ROW_END', 'changed_at', 'valid_until', 'status']}
                    
                    columns = ', '.join(clean_record.keys())
                    placeholders = ', '.join(['%s' for _ in clean_record])
                    query = f"REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
                    
                    self.engine.cursor.execute(query, list(clean_record.values()))
                    records_processed += 1
                
                # Note: 'added' records in restore_list would be deleted, but that's rare in selective restore
            
            return {
                'success': True,
                'records_processed': records_processed,
                'errors': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'records_processed': records_processed,
                'errors': [str(e)]
            }
    
    def _validate_batch_integrity(self, table: str, batch: List[Dict]) -> bool:
        """Validate integrity after batch execution"""
        
        try:
            # Basic check: ensure no duplicate primary keys
            pk_field = self.engine.tables[table]
            
            self.engine.cursor.execute(f"""
                SELECT {pk_field}, COUNT(*) as count 
                FROM {table} 
                GROUP BY {pk_field} 
                HAVING count > 1
            """)
            
            duplicates = self.engine.cursor.fetchall()
            return len(duplicates) == 0
            
        except:
            return False
    
    def _final_validation_check(self, table: str, restore_list: List[Dict]) -> bool:
        """Final validation after complete restore"""
        
        try:
            # Check that all expected records exist
            expected_ids = set()
            for item in restore_list:
                if item['type'] in ['deleted', 'modified']:
                    expected_ids.add(item['data']['id'])
            
            if expected_ids:
                pk_field = self.engine.tables[table]
                placeholders = ', '.join(['%s' for _ in expected_ids])
                
                self.engine.cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM {table} 
                    WHERE {pk_field} IN ({placeholders})
                """, list(expected_ids))
                
                result = self.engine.cursor.fetchone()
                actual_count = result['count'] if result else 0
                
                return actual_count == len(expected_ids)
            
            return True
            
        except:
            return False