from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.core.temporal_engine import TemporalEngine
from src.algorithms.diff_analyzer import DiffAnalyzer
from src.algorithms.health_scorer import HealthScorer

class SmartRestorePointFinder:
    """Intelligent algorithm to find optimal restore point"""
    
    def __init__(self, engine: TemporalEngine):
        """Initialize the smart restore point finder with database engine and analysis tools"""
        self.engine = engine  # Core temporal database engine for querying historical data
        self.diff_analyzer = DiffAnalyzer(engine)  # Tool for comparing data states between timestamps
        self.health_scorer = HealthScorer(engine)  # Tool for scoring data integrity at any timestamp
    
    def find_optimal_restore_point(self, table: str = 'airports', 
                                 disaster_type: Optional[str] = None) -> Dict:
        """
        Main algorithm: Find the best restore point using binary search
        
        Input: Table name where disaster occurred, optional disaster type
        Output: Dictionary with optimal timestamp, confidence score, and details
        """
        
        # Step 1: Define Search Window (24 hours back)
        # We search within last 24 hours as most disasters are recent and need quick recovery
        end_time = datetime.now()  # Current time (potentially corrupted state)
        start_time = end_time - timedelta(hours=24)  # 24 hours ago (likely clean state)
        
        print(f"🔍 Searching for optimal restore point...")
        print(f"   Search window: {start_time.strftime('%H:%M:%S')} to {end_time.strftime('%H:%M:%S')}")
        
        # Get current corrupted state as baseline for comparison
        # This helps us understand what we're trying to recover from
        current_state = self.engine.query_current(table)
        
        # Step 2: Binary Search Through Time - Core Innovation
        # Instead of checking every minute (1440 checks), binary search finds optimal point in ~12 iterations
        # This is the key algorithm that makes FlightVault fast and efficient
        optimal_timestamp, search_info = self._binary_search_through_time(
            table, start_time, end_time, current_state
        )
        
        # Step 3: Validate Stability of Restore Point
        # Ensure the selected timestamp is not in the middle of a transaction or bulk operation
        # This prevents restoring to an inconsistent state
        stability_check = self._validate_stability(table, optimal_timestamp)
        
        # Step 4: Calculate Final Confidence Score (0-100%)
        # Combines health score, stability, and boundary clarity to give user confidence in selection
        # High confidence (>80%) means safe to restore, low confidence (<70%) needs manual review
        confidence = self._calculate_confidence(
            search_info['health_score'], 
            stability_check, 
            search_info['boundary_clarity']
        )
        
        return {
            'optimal_timestamp': optimal_timestamp,
            'confidence_percentage': confidence,
            'health_score': search_info['health_score'],
            'validation_results': search_info['validation_details'],
            'reason_chosen': self._explain_choice(optimal_timestamp, search_info),
            'warnings': self._generate_warnings(confidence, stability_check),
            'alternative_timestamps': search_info.get('alternatives', []),
            'search_details': {
                'iterations': search_info['iterations'],
                'search_window_minutes': int((end_time - start_time).total_seconds() / 60),
                'boundary_found': search_info['boundary_clarity'] > 0.8
            }
        }
    
    def _binary_search_through_time(self, table: str, start_time: datetime, 
                                   end_time: datetime, current_state: List[Dict]) -> Tuple[datetime, Dict]:
        """
        Step 2: Binary search to efficiently find disaster boundary
        """
        
        # Initialize binary search variables
        best_timestamp = start_time  # Track the best restore point found so far
        best_health_score = 0  # Track the highest health score encountered
        iterations = 0  # Count search iterations for performance monitoring
        max_iterations = 15  # log2(1440 minutes) ≈ 11, so 15 provides safety margin
        
        # Binary search boundaries - these narrow down with each iteration
        current_start = start_time  # Left boundary of current search window
        current_end = end_time  # Right boundary of current search window
        
        search_log = []  # Log each iteration for debugging and analysis
        
        # Binary search loop - continues until we reach 5-minute precision or max iterations
        # 5 minutes precision is sufficient for most disaster recovery scenarios
        while (current_end - current_start).total_seconds() > 300 and iterations < max_iterations:
            iterations += 1
            
            # Calculate midpoint between current search boundaries
            # This is the timestamp we'll test in this iteration
            midpoint = current_start + (current_end - current_start) / 2
            
            # Health Validation at This Timestamp
            # Score data integrity (0-100) based on record count, required fields, foreign keys, etc.
            health_result = self.health_scorer.score_health(table, midpoint)
            health_score = health_result['score']  # Overall health score (0-100)
            validation_details = health_result.get('checks', {})  # Detailed breakdown of checks
            
            search_log.append({
                'timestamp': midpoint,
                'health_score': health_score,
                'iteration': iterations
            })
            
            print(f"   Iteration {iterations}: {midpoint.strftime('%H:%M:%S')} - Health: {health_score}/100")
            
            # Track best point found so far
            # We keep the timestamp with highest health score as our candidate restore point
            if health_score > best_health_score:
                best_timestamp = midpoint
                best_health_score = health_score
            
            # Determine search direction - this is the key binary search logic
            if health_score >= 80:  # Healthy data (80%+ health score)
                # Data is good here, so disaster happened later - search forward in time
                current_start = midpoint
            else:  # Corrupted data (< 80% health score)
                # Data is corrupted here, so disaster happened earlier - search backward in time
                current_end = midpoint
        
        # Step 4: Find Exact Disaster Boundary (minute precision)
        if (current_end - current_start).total_seconds() <= 600:  # Within 10 minutes
            best_timestamp = self._find_exact_boundary(table, current_start, current_end)
        
        # Calculate boundary clarity (how clear the disaster boundary is)
        boundary_clarity = min(best_health_score / 100.0, 1.0)
        
        return best_timestamp, {
            'health_score': best_health_score,
            'iterations': iterations,
            'boundary_clarity': boundary_clarity,
            'validation_details': validation_details if 'validation_details' in locals() else {},
            'search_log': search_log
        }
    
    def _validate_health_at_timestamp(self, table: str, timestamp: datetime) -> Tuple[int, Dict]:
        """
        Step 3: Health validation with multiple checks
        Returns health score (0-100) and detailed validation results
        """
        
        try:
            # Query data at this timestamp
            data_at_timestamp = self.engine.query_as_of(table, timestamp)
            
            if not data_at_timestamp:
                return 0, {'error': 'No data found at timestamp'}
            
            validation_results = {}
            total_score = 0
            
            # Check 1: Record Count Validation (25 points)
            expected_count = self._get_expected_record_count(table)
            actual_count = len(data_at_timestamp)
            
            if expected_count['min'] <= actual_count <= expected_count['max']:
                count_score = 25
            elif actual_count >= expected_count['min'] * 0.8:  # 80% of minimum acceptable
                count_score = 15
            elif actual_count > 0:
                count_score = 5
            else:
                count_score = 0
            
            total_score += count_score
            validation_results['record_count'] = {
                'score': count_score,
                'actual': actual_count,
                'expected_range': expected_count
            }
            
            # Check 2: No NULL Values in Required Fields (25 points)
            null_score = self._check_required_fields(data_at_timestamp, table)
            total_score += null_score
            validation_results['required_fields'] = {'score': null_score}
            
            # Check 3: Foreign Key Integrity (25 points)
            fk_score = self._validate_foreign_keys(table, timestamp, data_at_timestamp)
            total_score += fk_score
            validation_results['foreign_keys'] = {'score': fk_score}
            
            # Check 4: Data Distribution Validation (25 points)
            distribution_score = self._check_data_distribution(data_at_timestamp, table)
            total_score += distribution_score
            validation_results['data_distribution'] = {'score': distribution_score}
            
            return min(total_score, 100), validation_results
            
        except Exception as e:
            return 0, {'error': str(e)}
    
    def _get_expected_record_count(self, table: str) -> Dict:
        """Get expected record count range for validation"""
        
        # Get historical average from past week
        try:
            week_ago = datetime.now() - timedelta(days=7)
            historical_data = self.engine.query_as_of(table, week_ago)
            historical_count = len(historical_data)
            
            # Get current count (might be corrupted)
            current_data = self.engine.query_current(table)
            current_count = len(current_data)
            
            # Use historical as baseline, allow some variance
            baseline = max(historical_count, current_count)
            
            return {
                'min': int(baseline * 0.8),  # 80% of baseline
                'max': int(baseline * 1.2),  # 120% of baseline
                'baseline': baseline
            }
            
        except:
            # Fallback: assume current count is reasonable baseline
            current_data = self.engine.query_current(table)
            current_count = len(current_data)
            
            return {
                'min': max(1, int(current_count * 0.5)),
                'max': int(current_count * 2),
                'baseline': current_count
            }
    
    def _check_required_fields(self, data: List[Dict], table: str) -> int:
        """Check for NULL values in required fields"""
        
        required_fields = {
            'airports': ['airport_id', 'name'],
            'airlines': ['airline_id', 'name'],
            'routes': ['route_id']
        }
        
        if table not in required_fields or not data:
            return 25  # Full score if no requirements or no data to check
        
        null_violations = 0
        total_checks = len(data) * len(required_fields[table])
        
        for record in data:
            for field in required_fields[table]:
                if record.get(field) is None or record.get(field) == '':
                    null_violations += 1
        
        # Calculate score based on violation percentage
        if total_checks == 0:
            return 25
        
        violation_rate = null_violations / total_checks
        
        if violation_rate == 0:
            return 25
        elif violation_rate < 0.1:  # Less than 10% violations
            return 20
        elif violation_rate < 0.2:  # Less than 20% violations
            return 10
        else:
            return 0
    
    def _validate_foreign_keys(self, table: str, timestamp: datetime, data: List[Dict]) -> int:
        """Validate foreign key relationships at timestamp"""
        
        if table != 'routes' or not data:
            return 25  # Full score for non-route tables or empty data
        
        try:
            # Get airports at the same timestamp for FK validation
            airports_at_timestamp = self.engine.query_as_of('airports', timestamp)
            valid_airport_ids = {apt['airport_id'] for apt in airports_at_timestamp}
            
            valid_routes = 0
            total_routes = len(data)
            
            for route in data:
                source_id = route.get('source_airport_id')
                dest_id = route.get('destination_airport_id')
                
                # Check if both airports exist
                if (source_id in valid_airport_ids and dest_id in valid_airport_ids):
                    valid_routes += 1
            
            if total_routes == 0:
                return 25
            
            # Calculate score based on valid FK percentage
            valid_percentage = valid_routes / total_routes
            
            if valid_percentage >= 0.95:  # 95%+ valid
                return 25
            elif valid_percentage >= 0.8:  # 80%+ valid
                return 20
            elif valid_percentage >= 0.6:  # 60%+ valid
                return 10
            else:
                return 0
                
        except Exception:
            return 15  # Partial score if validation fails
    
    def _check_data_distribution(self, data: List[Dict], table: str) -> int:
        """Check if data distribution looks normal"""
        
        if not data:
            return 0
        
        score = 0
        
        # Check 1: Geographic distribution (for airports)
        if table == 'airports':
            cities = [record.get('city') for record in data if record.get('city')]
            countries = [record.get('country') for record in data if record.get('country')]
            
            unique_cities = len(set(cities))
            unique_countries = len(set(countries))
            
            # Good distribution means diverse cities and countries
            if len(cities) > 0:
                city_diversity = unique_cities / len(cities)
                if city_diversity > 0.3:  # 30%+ unique cities
                    score += 15
                elif city_diversity > 0.1:  # 10%+ unique cities
                    score += 10
                else:
                    score += 5
            
            if len(countries) > 0:
                country_diversity = unique_countries / len(countries)
                if country_diversity > 0.1:  # 10%+ unique countries
                    score += 10
                else:
                    score += 5
        else:
            score += 25  # Full score for non-airport tables
        
        return min(score, 25)
    
    def _find_exact_boundary(self, table: str, start_time: datetime, end_time: datetime) -> datetime:
        """Find exact minute when disaster occurred"""
        
        best_timestamp = start_time
        best_health = 0
        
        # Check every minute in the narrow window
        current = start_time
        while current <= end_time:
            health_score, _ = self._validate_health_at_timestamp(table, current)
            
            if health_score > best_health:
                best_timestamp = current
                best_health = health_score
            
            current += timedelta(minutes=1)
        
        return best_timestamp
    
    def _validate_stability(self, table: str, timestamp: datetime) -> Dict:
        """Step 5: Validate that restore point is stable (not mid-transaction)"""
        
        try:
            # Check data consistency around the timestamp
            before = timestamp - timedelta(minutes=2)
            after = timestamp + timedelta(minutes=2)
            
            data_before = self.engine.query_as_of(table, before)
            data_at = self.engine.query_as_of(table, timestamp)
            data_after = self.engine.query_as_of(table, after)
            
            # Stable if record counts are consistent
            count_before = len(data_before)
            count_at = len(data_at)
            count_after = len(data_after)
            
            is_stable = (count_before == count_at == count_after)
            
            return {
                'is_stable': is_stable,
                'count_variance': max(count_before, count_at, count_after) - min(count_before, count_at, count_after),
                'stability_score': 100 if is_stable else max(0, 100 - abs(count_at - count_before) * 10)
            }
            
        except Exception as e:
            return {
                'is_stable': False,
                'error': str(e),
                'stability_score': 50  # Neutral score if check fails
            }
    
    def _calculate_confidence(self, health_score: int, stability_check: Dict, boundary_clarity: float) -> int:
        """Calculate overall confidence percentage"""
        
        # Base confidence from health score
        confidence = health_score
        
        # Bonus for stability
        if stability_check.get('is_stable', False):
            confidence += 10
        else:
            confidence -= 5
        
        # Bonus for clear boundary detection
        if boundary_clarity > 0.9:
            confidence += 10
        elif boundary_clarity > 0.7:
            confidence += 5
        
        # Cap between 0 and 100
        return max(0, min(100, confidence))
    
    def _explain_choice(self, timestamp: datetime, search_info: Dict) -> str:
        """Generate human-readable explanation"""
        
        reasons = []
        
        if search_info['health_score'] >= 80:
            reasons.append("high data integrity")
        
        if search_info['boundary_clarity'] > 0.8:
            reasons.append("clear disaster boundary detected")
        
        if search_info['iterations'] <= 10:
            reasons.append("efficient search convergence")
        
        if not reasons:
            reasons.append("best available option in search window")
        
        return f"Selected {timestamp.strftime('%Y-%m-%d %H:%M:%S')} due to: " + ", ".join(reasons)
    
    def _generate_warnings(self, confidence: int, stability_check: Dict) -> List[str]:
        """Generate warnings about potential issues"""
        
        warnings = []
        
        if confidence < 70:
            warnings.append("Low confidence in restore point selection")
        
        if not stability_check.get('is_stable', True):
            warnings.append("Timestamp may be during active changes")
        
        if stability_check.get('count_variance', 0) > 5:
            warnings.append("Data count variance detected around timestamp")
        
        return warnings