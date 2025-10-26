"""
FlightVault REST API - Backend for Visual Disaster Recovery Tool
FastAPI-based REST API for temporal database operations
"""

from fastapi import FastAPI, HTTPException, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import traceback

from src.core.temporal_engine import create_engine, TemporalEngine
from src.algorithms.smart_restore_algorithm import SmartRestorePointFinder
from src.core.selective_restore import SelectiveRestoreEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flightvault_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FlightVault-API")

# Pydantic models for request/response validation
class RestoreRequest(BaseModel):
    table: str
    timestamp: Optional[str] = None
    dry_run: bool = False
    
    @validator('table')
    def validate_table(cls, v):
        if v not in ['airports', 'airlines', 'routes']:
            raise ValueError('Table must be one of: airports, airlines, routes')
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Invalid timestamp format. Use ISO format: YYYY-MM-DDTHH:MM:SS')
        return v

class SelectiveRestoreRequest(BaseModel):
    table: str
    timestamp: Optional[str] = None
    rules: Optional[List[Dict]] = None
    execute: bool = False

class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    timestamp: str
    version: str = "1.0.0"

# FastAPI app initialization
app = FastAPI(
    title="FlightVault API",
    description="Visual Disaster Recovery Tool - Git for your database using MariaDB System-Versioned Tables",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for database engine
def get_engine() -> TemporalEngine:
    """Dependency to get database engine"""
    try:
        return create_engine()
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        engine = create_engine()
        # Test database connection
        engine.query_current('airports', {'airport_id': 1})
        engine.close()
        
        return HealthResponse(
            status="ok",
            db_connected=True,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            db_connected=False,
            timestamp=datetime.now().isoformat()
        )

@app.get("/timeline")
async def get_timeline(
    table: str = Query(..., description="Table name"),
    hours: int = Query(24, description="Hours to look back"),
    engine: TemporalEngine = Depends(get_engine)
):
    """Get timeline of changes for visualization"""
    try:
        if table not in ['airports', 'airlines', 'routes']:
            raise HTTPException(status_code=400, detail="Invalid table name")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get audit trail
        audit_trail = engine.get_audit_trail(table, limit=1000)
        recent_changes = [
            {
                **entry,
                'changed_at': entry['changed_at'].isoformat(),
                'valid_until': entry['valid_until'].isoformat() if entry['valid_until'] else None
            }
            for entry in audit_trail 
            if entry['changed_at'] >= start_time
        ]
        
        # Group by 1-minute periods for better granularity
        timeline_data = []
        period_groups = {}
        
        for change in recent_changes:
            # Group by 1-minute periods
            period_key = change['changed_at'][:16]  # YYYY-MM-DDTHH:MM
            
            if period_key not in period_groups:
                period_groups[period_key] = []
            period_groups[period_key].append(change)
        
        for period, changes in sorted(period_groups.items()):
            timeline_data.append({
                'timestamp': period,
                'change_count': len(changes),
                'changes': changes[:10],
                'has_mass_changes': len(changes) > 50
            })
        
        return {
            'table': table,
            'hours': hours,
            'total_changes': len(recent_changes),
            'timeline': timeline_data
        }
        
    except Exception as e:
        logger.error(f"Timeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()

@app.get("/state")
async def get_state_at_timestamp(
    table: str = Query(..., description="Table name"),
    timestamp: str = Query(..., description="ISO timestamp"),
    limit: int = Query(25, description="Max records to return"),
    offset: int = Query(0, description="Offset for pagination"),
    engine: TemporalEngine = Depends(get_engine)
):
    """Get table state at specific timestamp"""
    try:
        if table not in ['airports', 'airlines', 'routes']:
            raise HTTPException(status_code=400, detail="Invalid table name")
        
        # Parse timestamp
        try:
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        # Query state at timestamp
        all_records = engine.query_as_of(table, ts)
        total_count = len(all_records)
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        records = all_records[start_idx:end_idx]
        
        return {
            'table': table,
            'timestamp': timestamp,
            'total_count': total_count,
            'record_count': len(records),
            'records': records,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'has_more': end_idx < total_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"State query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()

@app.get("/diff")
async def get_diff_between_states(
    table: str = Query(..., description="Table name"),
    before: str = Query(..., description="Before timestamp (ISO)"),
    after: Optional[str] = Query(None, description="After timestamp (ISO), defaults to now"),
    engine: TemporalEngine = Depends(get_engine)
):
    """Get diff between two timestamps"""
    try:
        if table not in ['airports', 'airlines', 'routes']:
            raise HTTPException(status_code=400, detail="Invalid table name")
        
        # Parse timestamps
        try:
            before_ts = datetime.fromisoformat(before.replace('Z', '+00:00'))
            after_ts = datetime.fromisoformat(after.replace('Z', '+00:00')) if after else datetime.now()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        # Get data at both timestamps
        before_data = engine.query_as_of(table, before_ts)
        after_data = engine.query_as_of(table, after_ts)
        
        # Calculate diff
        diff = engine.calculate_diff(before_data, after_data, table)
        
        return {
            'table': table,
            'before_timestamp': before,
            'after_timestamp': after or datetime.now().isoformat(),
            'before_count': len(before_data),
            'after_count': len(after_data),
            'diff': diff
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diff calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()

@app.get("/suggest-restore")
async def suggest_restore_point(
    table: str = Query(..., description="Table name"),
    engine: TemporalEngine = Depends(get_engine)
):
    """Get suggested restore point using smart algorithm"""
    try:
        if table not in ['airports', 'airlines', 'routes']:
            raise HTTPException(status_code=400, detail="Invalid table name")
        
        # Run smart restore point algorithm
        finder = SmartRestorePointFinder(engine)
        result = finder.find_optimal_restore_point(table)
        
        return {
            'table': table,
            'suggested_timestamp': result['optimal_timestamp'].isoformat(),
            'confidence_percentage': result['confidence_percentage'],
            'health_score': result['health_score'],
            'reason': result['reason_chosen'],
            'warnings': result['warnings'],
            'search_details': result['search_details']
        }
        
    except Exception as e:
        logger.error(f"Suggest restore error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()

@app.post("/restore")
async def execute_restore(
    request: RestoreRequest,
    engine: TemporalEngine = Depends(get_engine)
):
    """Execute database restore operation"""
    try:
        logger.info(f"Restore request: {request.dict()}")
        
        # Determine restore timestamp
        if request.timestamp:
            restore_ts = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
            logger.info(f"Using specified timestamp: {restore_ts}")
        else:
            # Use smart algorithm
            finder = SmartRestorePointFinder(engine)
            result = finder.find_optimal_restore_point(request.table)
            restore_ts = result['optimal_timestamp']
            logger.info(f"Smart algorithm selected: {restore_ts}")
        
        # Get data to restore
        historical_data = engine.query_as_of(request.table, restore_ts)
        current_data = engine.query_current(request.table)
        
        # Calculate what will be restored
        diff = engine.calculate_diff(current_data, historical_data, request.table)
        
        if request.dry_run:
            return {
                'dry_run': True,
                'table': request.table,
                'restore_timestamp': restore_ts.isoformat(),
                'records_to_restore': len(historical_data),
                'changes_preview': {
                    'will_add': len(diff['added']),
                    'will_update': len(diff['modified']),
                    'will_remove': len(diff['deleted'])
                },
                'preview': diff
            }
        
        # Execute restore
        restore_result = engine.restore_records(request.table, historical_data)
        
        if restore_result['success']:
            logger.info(f"Restore successful: {restore_result['restored_count']} records")
            
            # Verify final state
            final_data = engine.query_current(request.table)
            
            return {
                'success': True,
                'table': request.table,
                'restore_timestamp': restore_ts.isoformat(),
                'records_restored': restore_result['restored_count'],
                'final_count': len(final_data),
                'execution_time': 'immediate'
            }
        else:
            logger.error(f"Restore failed: {restore_result['errors']}")
            raise HTTPException(status_code=500, detail=f"Restore failed: {restore_result['errors']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore execution error: {e}")
        logger.error(f"Request data: {request.dict()}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()

@app.post("/selective-restore")
async def execute_selective_restore(
    request: SelectiveRestoreRequest,
    engine: TemporalEngine = Depends(get_engine)
):
    """Execute selective restore - surgical recovery"""
    try:
        logger.info(f"Selective restore request: {request.dict()}")
        
        # Initialize selective restore engine
        selective_engine = SelectiveRestoreEngine(engine)
        
        # Determine restore timestamp
        if request.timestamp:
            restore_ts = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
        else:
            finder = SmartRestorePointFinder(engine)
            result = finder.find_optimal_restore_point(request.table)
            restore_ts = result['optimal_timestamp']
        
        # Analyze changes
        change_set = selective_engine.analyze_changes(request.table, restore_ts)
        
        if change_set['summary']['total_changes'] == 0:
            return {
                'success': True,
                'message': 'No changes detected - nothing to restore',
                'changes': change_set
            }
        
        # Classify changes
        classification = selective_engine.classify_changes(change_set, request.rules)
        
        if not request.execute:
            # Preview mode
            return {
                'preview': True,
                'table': request.table,
                'restore_timestamp': restore_ts.isoformat(),
                'analysis': change_set,
                'classification': {
                    'keep_count': len(classification['keep_records']),
                    'restore_count': len(classification['restore_records']),
                    'uncertain_count': len(classification['uncertain_records'])
                }
            }
        
        # Execute selective restore
        if len(classification['restore_records']) == 0:
            return {
                'success': True,
                'message': 'No corrupted data identified - selective restore not needed'
            }
        
        # Validate dependencies
        validation = selective_engine.validate_dependencies(request.table, classification['restore_records'])
        
        if not validation['safe_to_restore']:
            raise HTTPException(
                status_code=400, 
                detail=f"Selective restore blocked: {validation['foreign_key_issues']}"
            )
        
        # Execute
        execution_result = selective_engine.execute_selective_restore(
            request.table, classification['restore_records'], validation
        )
        
        if execution_result['success']:
            logger.info(f"Selective restore successful: {execution_result['records_processed']} records")
            return {
                'success': True,
                'table': request.table,
                'records_processed': execution_result['records_processed'],
                'execution_time': execution_result['execution_time'],
                'batches_completed': execution_result['batches_completed']
            }
        else:
            logger.error(f"Selective restore failed: {execution_result['errors']}")
            raise HTTPException(status_code=500, detail=f"Selective restore failed: {execution_result['errors']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Selective restore error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()

@app.get("/tables")
async def get_available_tables(engine: TemporalEngine = Depends(get_engine)):
    """Get list of available tables with metadata"""
    try:
        tables_info = []
        
        for table_name in ['airports', 'airlines', 'routes']:
            current_data = engine.query_current(table_name)
            recent_changes = engine.get_audit_trail(table_name, limit=10)
            
            tables_info.append({
                'name': table_name,
                'current_count': len(current_data),
                'recent_changes': len(recent_changes),
                'last_change': recent_changes[0]['changed_at'].isoformat() if recent_changes else None,
                'primary_key': engine.tables[table_name]
            })
        
        return {
            'tables': tables_info,
            'total_tables': len(tables_info)
        }
        
    except Exception as e:
        logger.error(f"Tables info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()

# Additional utility endpoints

@app.get("/stats")
async def get_database_stats(engine: TemporalEngine = Depends(get_engine)):
    """Get overall database statistics"""
    try:
        stats = {}
        total_records = 0
        total_changes = 0
        
        for table in ['airports', 'airlines', 'routes']:
            current_data = engine.query_current(table)
            audit_trail = engine.get_audit_trail(table, limit=100)
            
            table_stats = {
                'current_records': len(current_data),
                'recent_changes': len(audit_trail),
                'last_change': audit_trail[0]['changed_at'].isoformat() if audit_trail else None
            }
            
            stats[table] = table_stats
            total_records += len(current_data)
            total_changes += len(audit_trail)
        
        return {
            'total_records': total_records,
            'total_recent_changes': total_changes,
            'tables': stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()

if __name__ == "__main__":
    import uvicorn
    import time
    import mariadb
    
    # Wait for database to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = mariadb.connect(**DATABASE_CONFIG)
            conn.close()
            print("✅ Database connection successful")
            break
        except Exception as e:
            print(f"⏳ Waiting for database... ({i+1}/{max_retries})")
            time.sleep(2)
    else:
        print("❌ Could not connect to database after 30 attempts")
        exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")