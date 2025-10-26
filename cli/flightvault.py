import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime, timedelta
from core.temporal_engine import create_engine
from algorithms.smart_restore_algorithm import SmartRestorePointFinder
from core.selective_restore import SelectiveRestoreEngine

class FlightVaultCLI:
    
    def __init__(self):
        self.engine = None
        self.smart_finder = None
        self.selective_restore = None
    
    def initialize(self):
        try:
            self.engine = create_engine()
            self.smart_finder = SmartRestorePointFinder(self.engine)
            self.selective_restore = SelectiveRestoreEngine(self.engine)
            return True
        except Exception as e:
            print(f"❌ Failed to initialize FlightVault: {e}")
            return False
    
    def timeline_explorer(self, table='airports', hours=24):
        print(f"📅 Timeline Explorer - Last {hours} hours of {table}")
        print("=" * 60)
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get audit trail to show timeline
        audit_trail = self.engine.get_audit_trail(table, limit=100)
        recent_changes = [
            entry for entry in audit_trail 
            if entry['changed_at'] >= start_time
        ]
        
        if not recent_changes:
            print("✅ No changes detected in timeline window")
            return
        
        print(f"📊 Found {len(recent_changes)} changes in last {hours} hours:")
        print()
        
        # Group changes by hour for timeline view
        hourly_changes = {}
        for change in recent_changes:
            hour_key = change['changed_at'].strftime('%Y-%m-%d %H:00')
            if hour_key not in hourly_changes:
                hourly_changes[hour_key] = []
            hourly_changes[hour_key].append(change)
        
        # Display timeline
        for hour, changes in sorted(hourly_changes.items()):
            status_counts = {}
            for change in changes:
                status = change['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            markers = []
            if status_counts.get('HISTORICAL', 0) > 10:
                markers.append("🚨 MASS CHANGES")
            elif status_counts.get('HISTORICAL', 0) > 0:
                markers.append("⚠️  Changes")
            
            marker_str = " ".join(markers) if markers else "✅ Normal"
            
            print(f"{hour} | {len(changes):3d} changes | {marker_str}")
        
        # Show current state
        current_data = self.engine.query_current(table)
        print(f"\n📈 Current state: {len(current_data)} records in {table}")
    
    def smart_diff_viewer(self, table='airports', timestamp_str=None):
        """Feature 2: Smart Diff Viewer"""
        print(f"🔍 Smart Diff Viewer for {table}")
        print("=" * 60)
        
        # Get comparison timestamps
        current_time = datetime.now()
        
        if timestamp_str:
            compare_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            # Default: compare with 1 hour ago
            compare_time = current_time - timedelta(hours=1)
        
        print(f"Comparing: {compare_time.strftime('%H:%M:%S')} vs Current")
        
        # Get data at both timestamps
        historical_data = self.engine.query_as_of(table, compare_time)
        current_data = self.engine.query_current(table)
        
        # Calculate diff
        diff = self.engine.calculate_diff(historical_data, current_data, table)
        
        print(f"\n📊 Diff Summary:")
        print(f"   Added: {diff['summary']['total_added']} records")
        print(f"   Deleted: {diff['summary']['total_deleted']} records")
        print(f"   Modified: {diff['summary']['total_modified']} records")
        
        # Show deleted records (red in real UI)
        if diff['deleted']:
            print(f"\n❌ Deleted Records ({len(diff['deleted'])}):")
            for record in diff['deleted'][:5]:
                name = record.get('name', f"ID {record.get(list(record.keys())[0])}")
                print(f"   - {name}")
            if len(diff['deleted']) > 5:
                print(f"   ... and {len(diff['deleted']) - 5} more")
        
        # Show added records (green in real UI)
        if diff['added']:
            print(f"\n✅ Added Records ({len(diff['added'])}):")
            for record in diff['added'][:5]:
                name = record.get('name', f"ID {record.get(list(record.keys())[0])}")
                print(f"   + {name}")
            if len(diff['added']) > 5:
                print(f"   ... and {len(diff['added']) - 5} more")
        
        # Show modified records with field-level changes
        if diff['modified']:
            print(f"\n🔄 Modified Records ({len(diff['modified'])}):")
            for mod in diff['modified'][:3]:
                name = mod['before'].get('name', f"ID {mod['before'].get(list(mod['before'].keys())[0])}")
                print(f"   ~ {name}")
                for change in mod['changes'][:3]:
                    print(f"     {change['field']}: '{change['before']}' → '{change['after']}'")
            if len(diff['modified']) > 3:
                print(f"   ... and {len(diff['modified']) - 3} more")
        
        return diff
    
    def intelligent_recovery(self, table='airports', dry_run=False, timestamp_str=None):
        """Feature 3: Intelligent One-Click Recovery"""
        print(f"🚀 Intelligent Recovery for {table}")
        print("=" * 60)
        
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        # Use specific timestamp or run smart algorithm
        if timestamp_str:
            restore_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            print(f"🎯 Using specified timestamp: {restore_timestamp}")
            result = {
                'optimal_timestamp': restore_timestamp,
                'confidence_percentage': 100,
                'health_score': 95,
                'reason_chosen': f'User-specified timestamp: {restore_timestamp}',
                'warnings': []
            }
        else:
            # Run the smart algorithm
            print("🧠 Running Smart Restore Point Algorithm...")
            result = self.smart_finder.find_optimal_restore_point(table)
        
        print(f"\n🎯 Algorithm Results:")
        print(f"   Optimal Timestamp: {result['optimal_timestamp']}")
        print(f"   Confidence: {result['confidence_percentage']}%")
        print(f"   Health Score: {result['health_score']}/100")
        print(f"   Reason: {result['reason_chosen']}")
        
        if result['warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in result['warnings']:
                print(f"   • {warning}")
        
        # Show what will be restored
        restore_timestamp = result['optimal_timestamp']
        historical_data = self.engine.query_as_of(table, restore_timestamp)
        current_data = self.engine.query_current(table)
        
        diff = self.engine.calculate_diff(current_data, historical_data, table)
        
        print(f"\n📋 Recovery Preview:")
        print(f"   Records to restore: {len(historical_data)}")
        print(f"   Will recover: {diff['summary']['total_added']} deleted records")
        print(f"   Will update: {diff['summary']['total_modified']} modified records")
        
        if dry_run:
            print("\n✅ Dry run complete - use --execute to perform actual recovery")
            return result
        
        # Execute recovery
        if result['confidence_percentage'] < 50:
            print(f"\n⚠️  Low confidence ({result['confidence_percentage']}%) - recovery not recommended")
            return result
        
        print(f"\n🔄 Executing recovery...")
        restore_result = self.engine.restore_records(table, historical_data)
        
        if restore_result['success']:
            print(f"✅ Recovery successful!")
            print(f"   Restored: {restore_result['restored_count']} records")
            
            # Verify recovery
            final_data = self.engine.query_current(table)
            print(f"   Final count: {len(final_data)} records")
        else:
            print(f"❌ Recovery failed!")
            for error in restore_result['errors']:
                print(f"   Error: {error}")
        
        return result
    
    def smart_algorithm_details(self, table='airports'):
        """Feature 4: Show Smart Restore Point Algorithm in action"""
        print(f"🧠 Smart Restore Point Algorithm - Detailed Analysis")
        print("=" * 60)
        
        print("Algorithm: Binary Search Through Temporal History")
        print("Innovation: Intelligent health scoring and boundary detection")
        print()
        
        # Run algorithm with detailed output
        result = self.smart_finder.find_optimal_restore_point(table)
        
        print(f"\n📊 Search Details:")
        search_details = result['search_details']
        print(f"   Search iterations: {search_details['iterations']}")
        print(f"   Search window: {search_details['search_window_minutes']} minutes")
        print(f"   Boundary found: {search_details['boundary_found']}")
        
        print(f"\n🔬 Validation Results:")
        validation = result['validation_results']
        for check, details in validation.items():
            if isinstance(details, dict) and 'score' in details:
                print(f"   {check}: {details['score']}/25 points")
        
        print(f"\n🎯 Final Assessment:")
        print(f"   Optimal timestamp: {result['optimal_timestamp']}")
        print(f"   Overall confidence: {result['confidence_percentage']}%")
        print(f"   Algorithm reasoning: {result['reason_chosen']}")
        
        return result
    
    def selective_restore_feature(self, table='airports', timestamp_str=None, rules=None):
        """Feature 5: Selective Restore - Surgical recovery of corrupted data"""
        print(f"🔧 Selective Restore for {table}")
        print("=" * 60)
        
        # Get restore timestamp
        if timestamp_str:
            restore_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            # Use smart algorithm to find optimal point
            print("🧠 Finding optimal restore point...")
            smart_result = self.smart_finder.find_optimal_restore_point(table)
            restore_timestamp = smart_result['optimal_timestamp']
            print(f"   Selected: {restore_timestamp.strftime('%H:%M:%S')} (Confidence: {smart_result['confidence_percentage']}%)")
        
        # Step 1: Analyze changes
        change_set = self.selective_restore.analyze_changes(table, restore_timestamp)
        
        if change_set['summary']['total_changes'] == 0:
            print("✅ No changes detected - nothing to restore")
            return
        
        # Step 2: Classify changes (using heuristics for CLI)
        print(f"\n🎯 Classifying changes using heuristic analysis...")
        classification = self.selective_restore.classify_changes(change_set, rules)
        
        # Show classification results
        print(f"\n📊 Classification Results:")
        print(f"   Keep (legitimate): {len(classification['keep_records'])} changes")
        print(f"   Restore (corrupted): {len(classification['restore_records'])} changes")
        print(f"   Uncertain: {len(classification['uncertain_records'])} changes")
        
        if len(classification['restore_records']) == 0:
            print("\n✅ No corrupted data identified - selective restore not needed")
            return
        
        # Show what will be restored
        print(f"\n📋 Restoration Preview:")
        restore_by_type = {}
        for item in classification['restore_records']:
            change_type = item['type']
            restore_by_type[change_type] = restore_by_type.get(change_type, 0) + 1
        
        for change_type, count in restore_by_type.items():
            print(f"   {change_type.title()}: {count} records")
        
        # Step 3: Validate dependencies
        validation = self.selective_restore.validate_dependencies(table, classification['restore_records'])
        
        print(f"\n🔗 Dependency Validation:")
        print(f"   Safe to restore: {validation['safe_to_restore']}")
        
        if validation['warnings']:
            print(f"   Warnings:")
            for warning in validation['warnings']:
                print(f"     ⚠️  {warning}")
        
        if not validation['safe_to_restore']:
            print(f"\n❌ Selective restore aborted due to dependency issues")
            for issue in validation['foreign_key_issues']:
                print(f"   • {issue}")
            return
        
        # Step 4: Execute selective restore
        print(f"\n🚀 Executing selective restore...")
        execution_result = self.selective_restore.execute_selective_restore(
            table, classification['restore_records'], validation
        )
        
        if execution_result['success']:
            print(f"\n✅ Selective restore completed successfully!")
            print(f"   Records processed: {execution_result['records_processed']}")
            print(f"   Batches completed: {execution_result['batches_completed']}")
            print(f"   Execution time: {execution_result['execution_time']:.2f}s")
            
            # Show final state
            final_data = self.engine.query_current(table)
            print(f"   Final record count: {len(final_data)}")
        else:
            print(f"\n❌ Selective restore failed!")
            for error in execution_result['errors']:
                print(f"   Error: {error}")
        
        return execution_result
    
    def status_check(self, table='airports'):
        """Quick status check"""
        print(f"📊 FlightVault Status - {table}")
        print("=" * 40)
        
        # Current state
        current_data = self.engine.query_current(table)
        print(f"Current records: {len(current_data)}")
        
        # Recent activity
        recent_changes = self.engine.get_audit_trail(table, limit=10)
        print(f"Recent changes: {len(recent_changes)}")
        
        # Check for potential disasters
        if len(recent_changes) > 0:
            latest_change = recent_changes[0]
            time_since = datetime.now() - latest_change['changed_at']
            
            if time_since.total_seconds() < 300:  # 5 minutes
                print("⚠️  Recent activity detected")
            else:
                print("✅ No recent activity")
        
        return {
            'current_count': len(current_data),
            'recent_changes': len(recent_changes)
        }

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="FlightVault - Visual Disaster Recovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Features:
  timeline     Show visual timeline of database changes
  diff         Smart diff viewer between timestamps  
  recover      Intelligent one-click recovery
  algorithm    Show smart algorithm in action
  selective    Selective restore - surgical recovery
  status       Quick status check

Examples:
  flightvault timeline                    # Show 24-hour timeline
  flightvault diff --timestamp 2024-01-01T12:00:00
  flightvault recover --dry-run           # Preview recovery
  flightvault recover --execute           # Execute recovery
  flightvault selective                   # Selective restore
  flightvault algorithm                   # Show algorithm details
        """
    )
    
    parser.add_argument('feature', 
                       choices=['timeline', 'diff', 'recover', 'algorithm', 'selective', 'status'],
                       help='FlightVault feature to use')
    
    parser.add_argument('--table', '-t', 
                       default='airports',
                       choices=['airports', 'airlines', 'routes'],
                       help='Table to operate on')
    
    parser.add_argument('--timestamp', 
                       help='Timestamp for comparison (ISO format)')
    
    parser.add_argument('--hours', 
                       type=int, 
                       default=24,
                       help='Hours for timeline view')
    
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Preview without making changes')
    
    parser.add_argument('--execute', 
                       action='store_true',
                       help='Execute actual recovery')
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = FlightVaultCLI()
    if not cli.initialize():
        sys.exit(1)
    
    try:
        # Execute feature
        if args.feature == 'timeline':
            cli.timeline_explorer(args.table, args.hours)
        
        elif args.feature == 'diff':
            cli.smart_diff_viewer(args.table, args.timestamp)
        
        elif args.feature == 'recover':
            dry_run = args.dry_run or not args.execute
            cli.intelligent_recovery(args.table, dry_run, args.timestamp)
        
        elif args.feature == 'algorithm':
            cli.smart_algorithm_details(args.table)
        
        elif args.feature == 'selective':
            cli.selective_restore_feature(args.table, args.timestamp)
        
        elif args.feature == 'status':
            cli.status_check(args.table)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    
    finally:
        if cli.engine:
            cli.engine.close()

if __name__ == "__main__":
    main()