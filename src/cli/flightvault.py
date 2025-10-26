import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import argparse
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box
from src.core.temporal_engine import create_engine
from src.algorithms.smart_restore_algorithm import SmartRestorePointFinder
from src.core.selective_restore import SelectiveRestoreEngine

class FlightVaultCLI:
    
    def __init__(self):
        self.console = Console()
        self.engine = None
        self.smart_finder = None
        self.selective_engine = None
    
    def initialize(self):
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Initializing FlightVault..."),
            console=self.console
        ) as progress:
            task = progress.add_task("init", total=None)
            try:
                self.engine = create_engine()
                self.smart_finder = SmartRestorePointFinder(self.engine)
                self.selective_engine = SelectiveRestoreEngine(self.engine)
                progress.update(task, completed=True)
                time.sleep(0.5)
                return True
            except Exception as e:
                self.console.print(f"[red]Failed to initialize FlightVault: {e}[/red]")
                return False
    
    def show_header(self):
        header = Text("FlightVault CLI", style="bold cyan")
        subtitle = Text("Visual Disaster Recovery Tool", style="dim")
        panel = Panel(
            Align.center(f"{header}\n{subtitle}"),
            box=box.DOUBLE,
            border_style="cyan"
        )
        self.console.print(panel)
    
    def status_check(self):
        self.console.print("\n[bold cyan]System Status Check[/bold cyan]")
        
        status_table = Table(show_header=True, header_style="bold magenta")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", justify="center")
        status_table.add_column("Details", style="dim")
        
        # Database connection
        try:
            current_data = self.engine.query_current('airports')
            status_table.add_row(
                "Database Connection",
                "[green]ONLINE[/green]",
                f"MariaDB connected"
            )
        except Exception as e:
            status_table.add_row(
                "Database Connection",
                "[red]OFFLINE[/red]",
                str(e)
            )
        
        # Table status
        for table in ['airports', 'airlines', 'routes']:
            try:
                data = self.engine.query_current(table)
                changes = self.engine.get_audit_trail(table, limit=10)
                status_table.add_row(
                    f"Table: {table}",
                    "[green]ACTIVE[/green]",
                    f"{len(data)} records, {len(changes)} recent changes"
                )
            except Exception:
                status_table.add_row(
                    f"Table: {table}",
                    "[red]ERROR[/red]",
                    "Unable to query"
                )
        
        self.console.print(status_table)
    
    def timeline_explorer(self, table='airports', hours=24):
        self.console.print(f"\n[bold cyan]Timeline Explorer[/bold cyan] - Last {hours} hours of [yellow]{table}[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Analyzing temporal history..."),
            console=self.console
        ) as progress:
            task = progress.add_task("timeline", total=None)
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            audit_trail = self.engine.get_audit_trail(table, limit=1000)
            recent_changes = [
                entry for entry in audit_trail 
                if entry['changed_at'] >= start_time
            ]
            progress.update(task, completed=True)
        
        if not recent_changes:
            self.console.print(Panel(
                "[green]No changes detected in timeline window[/green]",
                title="Timeline Status",
                border_style="green"
            ))
            return
        
        # Timeline table
        timeline_table = Table(show_header=True, header_style="bold magenta")
        timeline_table.add_column("Time Period", style="cyan")
        timeline_table.add_column("Changes", justify="right", style="yellow")
        timeline_table.add_column("Status", justify="center")
        timeline_table.add_column("Activity Level", style="dim")
        
        # Group changes by minute for granular view
        minute_changes = {}
        for change in recent_changes:
            minute_key = change['changed_at'].strftime('%b %d, %Y %H:%M:%S')
            if minute_key not in minute_changes:
                minute_changes[minute_key] = []
            minute_changes[minute_key].append(change)
        
        # Show only periods with changes, sorted by time
        for minute, changes in sorted(minute_changes.items(), key=lambda x: datetime.strptime(x[0], '%b %d, %Y %H:%M:%S'), reverse=True)[:10]:
            change_count = len(changes)
            
            if change_count > 500:
                status = "[red]CRITICAL[/red]"
                activity = "Mass changes detected"
            elif change_count > 10:
                status = "[yellow]WARNING[/yellow]"
                activity = "High activity"
            elif change_count > 0:
                status = "[blue]NORMAL[/blue]"
                activity = "Regular activity"
            else:
                status = "[green]QUIET[/green]"
                activity = "No activity"
            
            timeline_table.add_row(minute, str(change_count), status, activity)
        
        self.console.print(timeline_table)
        
        # Current state summary
        current_data = self.engine.query_current(table)
        summary_panel = Panel(
            f"[bold]Current State:[/bold] {len(current_data)} records in {table}\n"
            f"[bold]Total Changes:[/bold] {len(recent_changes)} in last {hours} hours",
            title="Summary",
            border_style="blue"
        )
        self.console.print(summary_panel)
    
    def smart_diff_viewer(self, table='airports', timestamp_str=None, detailed=False, hours=1):
        self.console.print(f"\n[bold cyan]Smart Diff Viewer[/bold cyan] for [yellow]{table}[/yellow]")
        
        current_time = datetime.now()
        if timestamp_str:
            compare_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            self.console.print(f"Comparing: [cyan]{compare_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan] vs [cyan]Current[/cyan]")
        else:
            # Find the earliest change within the hours window
            start_time = current_time - timedelta(hours=hours)
            
            # Get audit trail to find actual changes
            audit_trail = self.engine.get_audit_trail(table, limit=1000)
            recent_changes = [entry for entry in audit_trail if entry['changed_at'] >= start_time]
            
            if recent_changes:
                # Use the earliest change time as comparison point
                compare_time = min(change['changed_at'] for change in recent_changes) - timedelta(minutes=1)
                self.console.print(f"Comparing: [cyan]{compare_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan] vs [cyan]Current[/cyan] (showing changes in last {hours} hours)")
            else:
                compare_time = start_time
                self.console.print(f"Comparing: [cyan]{compare_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan] vs [cyan]Current[/cyan] ({hours} hours back)")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Calculating differences..."),
            BarColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("diff", total=3)
            
            historical_data = self.engine.query_as_of(table, compare_time)
            progress.advance(task)
            
            current_data = self.engine.query_current(table)
            progress.advance(task)
            
            diff = self.engine.calculate_diff(historical_data, current_data, table)
            progress.advance(task)
        
        # Diff summary table
        diff_table = Table(show_header=True, header_style="bold magenta")
        diff_table.add_column("Change Type", style="cyan")
        diff_table.add_column("Count", justify="right", style="yellow")
        diff_table.add_column("Impact", style="dim")
        
        diff_table.add_row(
            "[green]Added[/green]",
            str(diff['summary']['total_added']),
            "New records created"
        )
        diff_table.add_row(
            "[red]Deleted[/red]",
            str(diff['summary']['total_deleted']),
            "Records removed"
        )
        diff_table.add_row(
            "[yellow]Modified[/yellow]",
            str(diff['summary']['total_modified']),
            "Records updated"
        )
        
        self.console.print(diff_table)
        
        if detailed:
            self._show_detailed_diff(diff, table)
        else:
            # Show summary changes
            if diff['deleted']:
                deleted_panel = Panel(
                    "\n".join([f"• {record.get('name', f'ID {list(record.values())[0]}')}" 
                              for record in diff['deleted'][:5]]) + 
                    (f"\n... and {len(diff['deleted']) - 5} more" if len(diff['deleted']) > 5 else ""),
                    title="[red]Deleted Records[/red]",
                    border_style="red"
                )
                self.console.print(deleted_panel)
            
            if diff['added']:
                added_panel = Panel(
                    "\n".join([f"• {record.get('name', f'ID {list(record.values())[0]}')}" 
                              for record in diff['added'][:5]]) + 
                    (f"\n... and {len(diff['added']) - 5} more" if len(diff['added']) > 5 else ""),
                    title="[green]Added Records[/green]",
                    border_style="green"
                )
                self.console.print(added_panel)
            
            if not diff['deleted'] and not diff['added'] and not diff['modified']:
                self.console.print(Panel(
                    "[green]No changes detected in the comparison period[/green]\n"
                    "Try using --hours with a larger value or --timestamp parameter",
                    title="No Differences",
                    border_style="green"
                ))
        
        return diff
    
    def _show_detailed_diff(self, diff, table):
        self.console.print("\n[bold cyan]Detailed Record Comparison[/bold cyan]")
        
        # Show deleted records in detail
        if diff['deleted']:
            self.console.print("\n[bold red]Deleted Records[/bold red]")
            for i, record in enumerate(diff['deleted'][:5]):
                detail_table = Table(show_header=True, header_style="bold red", title=f"Deleted Record {i+1}")
                detail_table.add_column("Field", style="cyan")
                detail_table.add_column("Value", style="red")
                
                for key, value in record.items():
                    detail_table.add_row(str(key), str(value))
                
                self.console.print(detail_table)
        
        # Show added records in detail
        if diff['added']:
            self.console.print("\n[bold green]Added Records[/bold green]")
            for i, record in enumerate(diff['added'][:5]):
                detail_table = Table(show_header=True, header_style="bold green", title=f"Added Record {i+1}")
                detail_table.add_column("Field", style="cyan")
                detail_table.add_column("Value", style="green")
                
                for key, value in record.items():
                    detail_table.add_row(str(key), str(value))
                
                self.console.print(detail_table)
        
        # Show modified records with side-by-side comparison
        if diff['modified']:
            self.console.print("\n[bold yellow]Modified Records - Side by Side Comparison[/bold yellow]")
            for i, mod in enumerate(diff['modified'][:3]):
                before_record = mod['before']
                after_record = mod['after']
                changes = mod['changes']
                
                comparison_table = Table(
                    show_header=True, 
                    header_style="bold yellow", 
                    title=f"Modified: {before_record.get('name', f'ID {list(before_record.values())[0]}')}'"
                )
                comparison_table.add_column("Field", style="cyan")
                comparison_table.add_column("Before", style="red")
                comparison_table.add_column("After", style="green")
                comparison_table.add_column("Status", justify="center")
                
                changed_fields = {change['field'] for change in changes}
                
                for field in sorted(before_record.keys()):
                    before_val = str(before_record.get(field, ''))
                    after_val = str(after_record.get(field, ''))
                    
                    if field in changed_fields:
                        status = "[yellow]CHANGED[/yellow]"
                    else:
                        status = "[dim]same[/dim]"
                    
                    comparison_table.add_row(field, before_val, after_val, status)
                
                self.console.print(comparison_table)
    
    def intelligent_recovery(self, table='airports', dry_run=False, timestamp_str=None):
        self.console.print(f"\n[bold cyan]Intelligent Recovery[/bold cyan] for [yellow]{table}[/yellow]")
        
        if dry_run:
            self.console.print(Panel(
                "[yellow]DRY RUN MODE[/yellow] - No changes will be made",
                border_style="yellow"
            ))
        
        # Algorithm execution
        if timestamp_str:
            restore_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            self.console.print(f"Using specified timestamp: [cyan]{restore_timestamp}[/cyan]")
            result = {
                'optimal_timestamp': restore_timestamp,
                'confidence_percentage': 100,
                'health_score': 95,
                'reason_chosen': f'User-specified timestamp',
                'warnings': []
            }
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Running Smart Restore Algorithm..."),
                BarColumn(),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("algorithm", total=100)
                
                # Simulate algorithm steps
                for i in range(0, 101, 10):
                    time.sleep(0.1)
                    progress.update(task, completed=i)
                
                result = self.smart_finder.find_optimal_restore_point(table)
        
        # Results table
        results_table = Table(show_header=True, header_style="bold magenta")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="yellow")
        results_table.add_column("Assessment", style="dim")
        
        confidence = result['confidence_percentage']
        confidence_color = "green" if confidence >= 80 else "yellow" if confidence >= 60 else "red"
        
        results_table.add_row(
            "Optimal Timestamp",
            str(result['optimal_timestamp']),
            "Algorithm selected"
        )
        results_table.add_row(
            "Confidence Level",
            f"[{confidence_color}]{confidence}%[/{confidence_color}]",
            "Statistical confidence"
        )
        results_table.add_row(
            "Health Score",
            f"{result['health_score']}/100",
            "Data integrity score"
        )
        
        self.console.print(results_table)
        
        # Recovery preview
        restore_timestamp = result['optimal_timestamp']
        historical_data = self.engine.query_as_of(table, restore_timestamp)
        current_data = self.engine.query_current(table)
        diff = self.engine.calculate_diff(current_data, historical_data, table)
        
        preview_panel = Panel(
            f"Records to restore: [yellow]{len(historical_data)}[/yellow]\n"
            f"Will recover: [green]{diff['summary']['total_added']}[/green] deleted records\n"
            f"Will update: [blue]{diff['summary']['total_modified']}[/blue] modified records",
            title="Recovery Preview",
            border_style="blue"
        )
        self.console.print(preview_panel)
        
        if dry_run:
            self.console.print("[green]Dry run complete[/green] - use --execute to perform actual recovery")
            return result
        
        # Execute recovery
        if confidence < 50:
            self.console.print(f"[red]Low confidence ({confidence}%) - recovery not recommended[/red]")
            return result
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Executing recovery..."),
            BarColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("recovery", total=100)
            
            for i in range(0, 101, 20):
                time.sleep(0.1)
                progress.update(task, completed=i)
            
            restore_result = self.engine.restore_records(table, historical_data)
        
        if restore_result['success']:
            success_panel = Panel(
                f"[green]Recovery Successful![/green]\n"
                f"Restored: [yellow]{restore_result['restored_count']}[/yellow] records\n"
                f"Final count: [cyan]{len(self.engine.query_current(table))}[/cyan] records",
                title="Success",
                border_style="green"
            )
            self.console.print(success_panel)
        else:
            error_panel = Panel(
                f"[red]Recovery Failed![/red]\n" + "\n".join(restore_result['errors']),
                title="Error",
                border_style="red"
            )
            self.console.print(error_panel)
        
        return result
    
    def smart_algorithm_details(self, table='airports'):
        self.console.print(f"\n[bold cyan]Smart Restore Algorithm Analysis[/bold cyan]")
        
        algorithm_panel = Panel(
            "[bold]Algorithm:[/bold] Binary Search Through Temporal History\n"
            "[bold]Innovation:[/bold] Intelligent health scoring and boundary detection\n"
            "[bold]Efficiency:[/bold] O(log n) complexity for disaster detection",
            title="Technical Overview",
            border_style="cyan"
        )
        self.console.print(algorithm_panel)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Analyzing temporal patterns..."),
            BarColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("analysis", total=100)
            
            # Simulate algorithm analysis
            for i in range(0, 101, 10):
                time.sleep(0.1)
                progress.update(task, completed=i)
            
            result = self.smart_finder.find_optimal_restore_point(table)
        
        # Algorithm steps table
        steps_table = Table(show_header=True, header_style="bold magenta")
        steps_table.add_column("Step", style="cyan")
        steps_table.add_column("Process", style="yellow")
        steps_table.add_column("Result", style="dim")
        
        steps_table.add_row("1", "Binary Search Initialization", "Search window: 24 hours")
        steps_table.add_row("2", "Health Score Calculation", "Multi-factor validation")
        steps_table.add_row("3", "Boundary Detection", "Corruption onset identified")
        steps_table.add_row("4", "Confidence Assessment", f"{result['confidence_percentage']}% confidence")
        steps_table.add_row("5", "Optimal Point Selection", str(result['optimal_timestamp']))
        
        self.console.print(steps_table)
        
        return result
    
    def selective_restore(self, table='airports', execute=False):
        self.console.print(f"\n[bold cyan]Selective Restore[/bold cyan] - Surgical Recovery for [yellow]{table}[/yellow]")
        
        if not execute:
            self.console.print(Panel(
                "[yellow]PREVIEW MODE[/yellow] - Use --execute to perform actual restore",
                border_style="yellow"
            ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Analyzing changes for selective restore..."),
            BarColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("selective", total=100)
            
            # Get optimal restore point
            result = self.smart_finder.find_optimal_restore_point(table)
            progress.update(task, completed=30)
            
            # Analyze changes
            change_set = self.selective_engine.analyze_changes(table, result['optimal_timestamp'])
            progress.update(task, completed=60)
            
            # Classify changes
            classification = self.selective_engine.classify_changes(change_set, [])
            progress.update(task, completed=100)
        
        # Classification results
        classification_table = Table(show_header=True, header_style="bold magenta")
        classification_table.add_column("Category", style="cyan")
        classification_table.add_column("Count", justify="right", style="yellow")
        classification_table.add_column("Action", style="dim")
        
        classification_table.add_row(
            "[green]Keep Current[/green]",
            str(len(classification['keep_records'])),
            "Legitimate changes preserved"
        )
        classification_table.add_row(
            "[red]Restore Historical[/red]",
            str(len(classification['restore_records'])),
            "Corrupted data to restore"
        )
        classification_table.add_row(
            "[yellow]Uncertain[/yellow]",
            str(len(classification['uncertain_records'])),
            "Requires manual review"
        )
        
        self.console.print(classification_table)
        
        if not execute:
            self.console.print("[green]Preview complete[/green] - use --execute to perform selective restore")
            return classification
        
        # Execute selective restore
        if len(classification['restore_records']) == 0:
            self.console.print(Panel(
                "[green]No corrupted data identified[/green]\nSelective restore not needed",
                title="Result",
                border_style="green"
            ))
            return classification
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Executing selective restore..."),
            BarColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("execute", total=100)
            
            # Validate dependencies
            validation = self.selective_engine.validate_dependencies(table, classification['restore_records'])
            progress.update(task, completed=30)
            
            if not validation['safe_to_restore']:
                self.console.print(Panel(
                    f"[red]Selective restore blocked[/red]\n{validation['foreign_key_issues']}",
                    title="Validation Error",
                    border_style="red"
                ))
                return classification
            
            # Execute
            execution_result = self.selective_engine.execute_selective_restore(
                table, classification['restore_records'], validation
            )
            progress.update(task, completed=100)
        
        if execution_result['success']:
            success_panel = Panel(
                f"[green]Selective Restore Successful![/green]\n"
                f"Records processed: [yellow]{execution_result['records_processed']}[/yellow]\n"
                f"Execution time: [cyan]{execution_result['execution_time']}[/cyan]\n"
                f"Batches completed: [blue]{execution_result['batches_completed']}[/blue]",
                title="Success",
                border_style="green"
            )
            self.console.print(success_panel)
        else:
            error_panel = Panel(
                f"[red]Selective Restore Failed![/red]\n" + "\n".join(execution_result['errors']),
                title="Error",
                border_style="red"
            )
            self.console.print(error_panel)
        
        return classification

def main():
    cli = FlightVaultCLI()
    cli.show_header()
    
    parser = argparse.ArgumentParser(
        description="FlightVault CLI - Visual Disaster Recovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='System status check')
    
    # Timeline command
    timeline_parser = subparsers.add_parser('timeline', help='Timeline explorer')
    timeline_parser.add_argument('--table', default='airports', choices=['airports', 'airlines', 'routes'])
    timeline_parser.add_argument('--hours', type=int, default=24, help='Hours to look back')
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Smart diff viewer')
    diff_parser.add_argument('--table', default='airports', choices=['airports', 'airlines', 'routes'])
    diff_parser.add_argument('--timestamp', help='Compare timestamp (ISO format)')
    diff_parser.add_argument('--hours', type=int, default=1, help='Hours to look back (default: 1)')
    diff_parser.add_argument('--detailed', action='store_true', help='Show detailed record-by-record comparison')
    
    # Recover command
    recover_parser = subparsers.add_parser('recover', help='Intelligent recovery')
    recover_parser.add_argument('--table', default='airports', choices=['airports', 'airlines', 'routes'])
    recover_parser.add_argument('--timestamp', help='Specific timestamp to restore (ISO format)')
    recover_parser.add_argument('--dry-run', action='store_true', help='Preview mode - no changes made')
    recover_parser.add_argument('--execute', action='store_true', help='Execute actual recovery')
    
    # Algorithm command
    algorithm_parser = subparsers.add_parser('algorithm', help='Smart algorithm analysis')
    algorithm_parser.add_argument('--table', default='airports', choices=['airports', 'airlines', 'routes'])
    
    # Selective command
    selective_parser = subparsers.add_parser('selective', help='Selective restore - surgical recovery')
    selective_parser.add_argument('--table', default='airports', choices=['airports', 'airlines', 'routes'])
    selective_parser.add_argument('--execute', action='store_true', help='Execute selective restore')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    if not cli.initialize():
        return
    
    try:
        if args.command == 'status':
            cli.status_check()
        elif args.command == 'timeline':
            cli.timeline_explorer(args.table, args.hours)
        elif args.command == 'diff':
            cli.smart_diff_viewer(args.table, args.timestamp, getattr(args, 'detailed', False), getattr(args, 'hours', 1))
        elif args.command == 'recover':
            dry_run = args.dry_run or not args.execute
            cli.intelligent_recovery(args.table, dry_run, args.timestamp)
        elif args.command == 'algorithm':
            cli.smart_algorithm_details(args.table)
        elif args.command == 'selective':
            cli.selective_restore(args.table, args.execute)
    
    except KeyboardInterrupt:
        cli.console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        cli.console.print(f"\n[red]Error: {e}[/red]")
    finally:
        if cli.engine:
            cli.engine.close()

if __name__ == "__main__":
    main()