#!/usr/bin/env python3
"""
Database manager for .clinerules logger.
Enhanced with automatic interaction tracking capabilities.
"""

import os
import sqlite3
import threading
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

import sys
import os
import importlib.util

# Add paths for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(os.path.dirname(current_dir), "utils")
sys.path.insert(0, utils_dir)

# Define module loading function
def load_module_from_path(module_path, module_name):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

try:
    from config import config
except ImportError:
    # Fallback to relative import if absolute import fails
    from ..utils.config import config

# Handle both absolute and relative imports for schema
schema_path = os.path.join(current_dir, "schema.py")
try:
    # Try direct import first
    schema_module = load_module_from_path(schema_path, "schema")
    Base = schema_module.Base
    create_tables = schema_module.create_tables
    ContextWindow = schema_module.ContextWindow
    Rule = schema_module.Rule
    Component = schema_module.Component
    RuleExecution = schema_module.RuleExecution
    ComponentExecution = schema_module.ComponentExecution
    Notification = schema_module.Notification
    FileInteraction = schema_module.FileInteraction
    SystemEvent = schema_module.SystemEvent
except (NameError, ImportError):
    # Fall back to relative import if direct import fails
    try:
        from .schema import (
            Base, create_tables, ContextWindow, 
            Rule, Component, RuleExecution, ComponentExecution, Notification,
            FileInteraction, SystemEvent
        )
    except ImportError:
        # If all else fails, try one more approach with absolute import
        sys.path.insert(0, os.path.dirname(current_dir))
        from db.schema import (
            Base, create_tables, ContextWindow, 
            Rule, Component, RuleExecution, ComponentExecution, Notification,
            FileInteraction, SystemEvent
        )

class DatabaseManager:
    """Manager for database connections and operations."""
    
    _instance = None
    _lock = threading.Lock()
    _engine = None
    _session_factory = None
    _scoped_session = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one database manager instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialize_db()
            return cls._instance
    
    def _initialize_db(self):
        """Initialize the database connection and tables."""
        db_path = config.get('database', 'path')
        
        # Create parent directory if it doesn't exist
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        
        # Create SQLAlchemy engine with connection pooling
        self._engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600
        )
        
        # Create tables if they don't exist
        create_tables(self._engine)
        
        # Create session factory
        self._session_factory = sessionmaker(bind=self._engine)
        self._scoped_session = scoped_session(self._session_factory)
    
    def get_session(self):
        """Get a new database session."""
        return self._scoped_session()
    
    def close_session(self, session):
        """Close a database session."""
        if session:
            session.close()
    
    def commit_session(self, session):
        """Commit changes in a session and handle errors."""
        try:
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error committing session: {e}")
            return False
    
    def import_legacy_log(self):
        """Import data from the legacy log file."""
        if not config.get('legacy', 'import_on_startup'):
            return
            
        legacy_log_path = config.get('legacy', 'log_path')
        if not os.path.exists(legacy_log_path):
            return
            
        try:
            session = self.get_session()
            
            with open(legacy_log_path, 'r') as f:
                lines = f.readlines()
                
                # Skip header and separator lines
                for line in lines[2:]:
                    if not line.strip() or line.startswith('-'):
                        continue
                        
                    parts = [part.strip() for part in line.split('|')]
                    if len(parts) != 5:
                        continue
                        
                    checkpoint_id, timestamp_str, task_context, clinerule, component = parts
                    
                    try:
                        # Parse timestamp
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        
                        # Find or create rule
                        rule = session.query(Rule).filter_by(rule_name=clinerule).first()
                        if not rule:
                            rule = Rule(
                                rule_name=clinerule,
                                first_seen=timestamp,
                                execution_count=0
                            )
                            session.add(rule)
                            session.flush()  # To get the rule ID
                        
                        # Find or create component
                        comp = session.query(Component).filter_by(
                            rule_id=rule.id, 
                            component_name=component
                        ).first()
                        
                        if not comp:
                            comp = Component(
                                rule_id=rule.id,
                                component_name=component,
                                execution_count=0
                            )
                            session.add(comp)
                            session.flush()  # To get the component ID
                        
                        # Create dummy context window for legacy data
                        dummy_context = ContextWindow(
                            session_id=f"legacy_{timestamp.strftime('%Y%m%d%H%M%S')}",
                            start_time=timestamp,
                            end_time=timestamp,
                            status='completed'
                        )
                        session.add(dummy_context)
                        session.flush()
                        
                        # Create rule execution
                        rule_exec = RuleExecution(
                            context_window_id=dummy_context.id,
                            rule_id=rule.id,
                            execution_time=timestamp,
                            task_document=task_context,
                            notes="Imported from legacy log"
                        )
                        session.add(rule_exec)
                        session.flush()
                        
                        # Create component execution
                        comp_exec = ComponentExecution(
                            rule_execution_id=rule_exec.id,
                            component_id=comp.id,
                            execution_time=timestamp,
                            notes="Imported from legacy log"
                        )
                        session.add(comp_exec)
                        
                        # Update counts
                        rule.execution_count += 1
                        comp.execution_count += 1
                        
                    except Exception as e:
                        print(f"Error importing legacy log entry: {e}")
                        continue
            
            # Commit changes
            self.commit_session(session)
            
            # Update config to not import on next startup
            config.set('legacy', 'import_on_startup', False)
            
        except Exception as e:
            print(f"Error importing legacy log: {e}")
        finally:
            self.close_session(session)
    
    # Context Window Management
    
    def start_context_window(self, session_id):
        """Start a new context window session."""
        session = self.get_session()
        try:
            # Check if session already exists
            existing = session.query(ContextWindow).filter_by(
                session_id=session_id,
                status='active'
            ).first()
            
            if existing:
                return existing
            
            # Create new context window
            context_window = ContextWindow(
                session_id=session_id,
                start_time=datetime.now(),
                status='active'
            )
            session.add(context_window)
            self.commit_session(session)
            return context_window
        finally:
            self.close_session(session)
    
    def update_context_window(self, session_id, token_count=None, status=None):
        """Update an existing context window."""
        session = self.get_session()
        try:
            context_window = session.query(ContextWindow).filter_by(
                session_id=session_id,
                status='active'
            ).first()
            
            if not context_window:
                return None
            
            if token_count is not None:
                context_window.token_count = token_count
            
            if status is not None:
                context_window.status = status
                if status == 'completed':
                    context_window.end_time = datetime.now()
            
            self.commit_session(session)
            return context_window
        finally:
            self.close_session(session)
    
    def get_active_context_window(self, session_id):
        """Get the active context window for a session."""
        session = self.get_session()
        try:
            return session.query(ContextWindow).filter_by(
                session_id=session_id,
                status='active'
            ).first()
        finally:
            self.close_session(session)
    
    # Rule Management
    
    def get_or_create_rule(self, rule_name, file_path=None, description=None):
        """Get an existing rule or create a new one."""
        session = self.get_session()
        try:
            rule = session.query(Rule).filter_by(rule_name=rule_name).first()
            
            if not rule:
                rule = Rule(
                    rule_name=rule_name,
                    file_path=file_path,
                    description=description,
                    execution_count=0
                )
                session.add(rule)
                self.commit_session(session)
            
            return rule
        finally:
            self.close_session(session)
    
    # Component Management
    
    def get_or_create_component(self, rule_id, component_name, description=None):
        """Get an existing component or create a new one."""
        session = self.get_session()
        try:
            component = session.query(Component).filter_by(
                rule_id=rule_id,
                component_name=component_name
            ).first()
            
            if not component:
                component = Component(
                    rule_id=rule_id,
                    component_name=component_name,
                    description=description,
                    execution_count=0
                )
                session.add(component)
                self.commit_session(session)
            
            return component
        finally:
            self.close_session(session)
    
    # Execution Logging
    
    def log_rule_execution(self, context_window_id, rule_id, task_document=None, notes=None):
        """Log a rule execution event."""
        session = self.get_session()
        try:
            # Create rule execution record
            rule_exec = RuleExecution(
                context_window_id=context_window_id,
                rule_id=rule_id,
                task_document=task_document,
                notes=notes
            )
            session.add(rule_exec)
            
            # Update rule execution count
            rule = session.query(Rule).filter_by(id=rule_id).first()
            if rule:
                rule.execution_count += 1
            
            self.commit_session(session)
            return rule_exec
        finally:
            self.close_session(session)
    
    def log_component_execution(self, rule_execution_id, component_id, notes=None):
        """Log a component execution event."""
        session = self.get_session()
        try:
            # Create component execution record
            comp_exec = ComponentExecution(
                rule_execution_id=rule_execution_id,
                component_id=component_id,
                notes=notes
            )
            session.add(comp_exec)
            
            # Update component execution count
            component = session.query(Component).filter_by(id=component_id).first()
            if component:
                component.execution_count += 1
            
            self.commit_session(session)
            return comp_exec
        finally:
            self.close_session(session)
    
    # Notification Management
    
    def create_notification(self, title, message, pattern_type, priority=1, confidence=1.0):
        """Create a new notification."""
        session = self.get_session()
        try:
            notification = Notification(
                title=title,
                message=message,
                pattern_type=pattern_type,
                priority=priority,
                confidence=confidence
            )
            session.add(notification)
            self.commit_session(session)
            return notification
        finally:
            self.close_session(session)
    
    def get_unread_notifications(self):
        """Get all unread notifications."""
        session = self.get_session()
        try:
            return session.query(Notification).filter_by(read=False).all()
        finally:
            self.close_session(session)
    
    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        session = self.get_session()
        try:
            notification = session.query(Notification).filter_by(id=notification_id).first()
            if notification:
                notification.read = True
                self.commit_session(session)
                return True
            return False
        finally:
            self.close_session(session)
            
    # File Interaction Logging
    
    def log_file_interaction(self, rule_id, interaction_type, metadata=None, context_window_id=None, 
                            application="unknown", user_initiated=False):
        """Log a file interaction event."""
        session = self.get_session()
        try:
            interaction = FileInteraction(
                rule_id=rule_id,
                context_window_id=context_window_id,
                interaction_type=interaction_type,
                application=application,
                user_initiated=user_initiated
            )
            
            # Set meta_data if provided
            if metadata:
                interaction.set_metadata(metadata)
                
            session.add(interaction)
            self.commit_session(session)
            return interaction
        finally:
            self.close_session(session)
    
    def get_rule_interactions(self, rule_id=None, interaction_type=None, limit=100):
        """Get file interactions for a specific rule or interaction type."""
        session = self.get_session()
        try:
            query = session.query(FileInteraction)
            
            if rule_id:
                query = query.filter(FileInteraction.rule_id == rule_id)
                
            if interaction_type:
                query = query.filter(FileInteraction.interaction_type == interaction_type)
                
            return query.order_by(desc(FileInteraction.interaction_time)).limit(limit).all()
        finally:
            self.close_session(session)
    
    def get_recent_interactions(self, limit=50):
        """Get recent file interactions across all rules."""
        session = self.get_session()
        try:
            return session.query(FileInteraction)\
                .order_by(desc(FileInteraction.interaction_time))\
                .limit(limit)\
                .all()
        finally:
            self.close_session(session)
    
    # System Event Logging
    
    def log_system_event(self, event_type, source="system", details=None):
        """Log a system event."""
        session = self.get_session()
        try:
            event = SystemEvent(
                event_type=event_type,
                source=source
            )
            
            # Set event_details if provided
            if details:
                event.set_details(details)
                
            session.add(event)
            self.commit_session(session)
            return event
        finally:
            self.close_session(session)
    
    def get_recent_system_events(self, event_type=None, source=None, limit=50):
        """Get recent system events, optionally filtered by type or source."""
        session = self.get_session()
        try:
            query = session.query(SystemEvent)
            
            if event_type:
                query = query.filter(SystemEvent.event_type == event_type)
                
            if source:
                query = query.filter(SystemEvent.source == source)
                
            return query.order_by(desc(SystemEvent.event_time)).limit(limit).all()
        finally:
            self.close_session(session)
    
    def get_interaction_statistics(self, days=30):
        """Get statistics about file interactions."""
        from datetime import timedelta
        
        session = self.get_session()
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get interaction counts by type
            interaction_counts = session.query(
                FileInteraction.interaction_type,
                func.count(FileInteraction.id).label('count')
            )\
            .filter(FileInteraction.interaction_time >= start_date)\
            .group_by(FileInteraction.interaction_type)\
            .all()
            
            # Get most active rules
            active_rules = session.query(
                Rule.rule_name,
                func.count(FileInteraction.id).label('interaction_count')
            )\
            .join(FileInteraction, Rule.id == FileInteraction.rule_id)\
            .filter(FileInteraction.interaction_time >= start_date)\
            .group_by(Rule.id)\
            .order_by(desc('interaction_count'))\
            .limit(10)\
            .all()
            
            # Get application usage
            app_usage = session.query(
                FileInteraction.application,
                func.count(FileInteraction.id).label('count')
            )\
            .filter(FileInteraction.interaction_time >= start_date)\
            .group_by(FileInteraction.application)\
            .all()
            
            return {
                'period_days': days,
                'interaction_counts': {t: c for t, c in interaction_counts},
                'active_rules': [{'rule': r, 'count': c} for r, c in active_rules],
                'app_usage': {a if a else 'unknown': c for a, c in app_usage}
            }
        finally:
            self.close_session(session)

# Create singleton instance
db_manager = DatabaseManager()
