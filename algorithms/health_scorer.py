"""
Health Scorer - Validate data quality at any timestamp
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from core.temporal_engine import TemporalEngine

class HealthScorer:
    """Score data health and integrity at timestamps"""
    
    def __init__(self, engine: TemporalEngine):
        self.engine = engine
    
    def score_health(self, table: str, timestamp: datetime) -> Dict:
        """Score data health at specific timestamp"""
        
        try:
            data = self.engine.query_as_of(table, timestamp)
            
            if not data:
                return {'score': 0, 'error': 'No data found'}
            
            # Run all health checks
            checks = {
                'record_count': self._check_record_count(data, table),
                'required_fields': self._check_required_fields(data, table),
                'foreign_keys': self._check_foreign_keys(data, table, timestamp),
                'data_distribution': self._check_data_distribution(data, table)
            }
            
            # Calculate total score
            total_score = sum(check['score'] for check in checks.values())
            
            return {
                'score': min(total_score, 100),
                'timestamp': timestamp,
                'checks': checks,
                'health_level': self._get_health_level(total_score)
            }
            
        except Exception as e:
            return {'score': 0, 'error': str(e)}
    
    def _check_record_count(self, data: List[Dict], table: str) -> Dict:
        """Validate record count is reasonable"""
        
        expected = self._get_expected_count(table)
        actual = len(data)
        
        if expected['min'] <= actual <= expected['max']:
            score = 25
            status = 'healthy'
        elif actual >= expected['min'] * 0.8:
            score = 15
            status = 'warning'
        else:
            score = 0
            status = 'critical'
        
        return {
            'score': score,
            'status': status,
            'actual_count': actual,
            'expected_range': expected
        }
    
    def _check_required_fields(self, data: List[Dict], table: str) -> Dict:
        """Check for NULL values in required fields"""
        
        required_fields = {
            'airports': ['airport_id', 'name'],
            'airlines': ['airline_id', 'name'],
            'routes': ['route_id']
        }
        
        if table not in required_fields:
            return {'score': 25, 'status': 'healthy'}
        
        violations = 0
        total_checks = len(data) * len(required_fields[table])
        
        for record in data:
            for field in required_fields[table]:
                if not record.get(field):
                    violations += 1
        
        if violations == 0:
            score, status = 25, 'healthy'
        elif violations / total_checks < 0.1:
            score, status = 15, 'warning'
        else:
            score, status = 0, 'critical'
        
        return {
            'score': score,
            'status': status,
            'violations': violations,
            'total_checks': total_checks
        }
    
    def _check_foreign_keys(self, data: List[Dict], table: str, timestamp: datetime) -> Dict:
        """Validate foreign key integrity"""
        
        if table != 'routes':
            return {'score': 25, 'status': 'healthy'}
        
        try:
            airports = self.engine.query_as_of('airports', timestamp)
            valid_ids = {apt['airport_id'] for apt in airports}
            
            valid_routes = 0
            for route in data:
                if (route.get('source_airport_id') in valid_ids and 
                    route.get('destination_airport_id') in valid_ids):
                    valid_routes += 1
            
            valid_pct = valid_routes / len(data) if data else 1
            
            if valid_pct >= 0.95:
                score, status = 25, 'healthy'
            elif valid_pct >= 0.8:
                score, status = 15, 'warning'
            else:
                score, status = 0, 'critical'
            
            return {
                'score': score,
                'status': status,
                'valid_routes': valid_routes,
                'total_routes': len(data),
                'valid_percentage': valid_pct * 100
            }
            
        except:
            return {'score': 10, 'status': 'unknown', 'error': 'FK check failed'}
    
    def _check_data_distribution(self, data: List[Dict], table: str) -> Dict:
        """Check data distribution patterns"""
        
        if table == 'airports':
            cities = [r.get('city') for r in data if r.get('city')]
            countries = [r.get('country') for r in data if r.get('country')]
            
            city_diversity = len(set(cities)) / len(cities) if cities else 0
            country_diversity = len(set(countries)) / len(countries) if countries else 0
            
            score = 0
            if city_diversity > 0.3:
                score += 15
            elif city_diversity > 0.1:
                score += 10
            else:
                score += 5
            
            if country_diversity > 0.1:
                score += 10
            else:
                score += 5
            
            status = 'healthy' if score >= 20 else 'warning' if score >= 10 else 'critical'
            
            return {
                'score': score,
                'status': status,
                'city_diversity': city_diversity,
                'country_diversity': country_diversity
            }
        
        return {'score': 25, 'status': 'healthy'}
    
    def _get_expected_count(self, table: str) -> Dict:
        """Get expected record count range"""
        
        try:
            current = self.engine.query_current(table)
            baseline = len(current)
            
            return {
                'min': int(baseline * 0.8),
                'max': int(baseline * 1.2),
                'baseline': baseline
            }
        except:
            return {'min': 1, 'max': 10000, 'baseline': 1000}
    
    def _get_health_level(self, score: int) -> str:
        """Convert score to health level"""
        if score >= 80:
            return 'healthy'
        elif score >= 60:
            return 'warning'
        else:
            return 'critical'