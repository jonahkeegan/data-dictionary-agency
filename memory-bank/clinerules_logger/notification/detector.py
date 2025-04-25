#!/usr/bin/env python3
"""
Pattern detector for .clinerules notification system.
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc, asc

from ..db.manager import db_manager
from ..db.schema import (
    ContextWindow, Rule, Component, 
    RuleExecution, ComponentExecution, Notification
)
from ..utils.config import config

class PatternDetector:
    """Detects patterns in rule execution data and generates notifications."""
    
    @staticmethod
    def detect_frequent_rule_usage(threshold=None, window_hours=None, create_notification=True):
        """Detect rules that are used frequently within a time window."""
        # Get configuration
        threshold = threshold or config.get('notification', 'threshold')
        window_hours = window_hours or config.get('notification', 'window_hours')
        
        session = db_manager.get_session()
        try:
            # Set time range
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=window_hours)
            
            # Query for rules used more than threshold times in the window
            results = session.query(
                Rule.id,
                Rule.rule_name,
                func.count(RuleExecution.id).label('execution_count')
            )\
            .join(RuleExecution, Rule.id == RuleExecution.rule_id)\
            .filter(RuleExecution.execution_time >= start_date)\
            .group_by(Rule.id)\
            .having(func.count(RuleExecution.id) >= threshold)\
            .all()
            
            frequent_rules = []
            for rule_id, rule_name, count in results:
                # Check if we already have a notification for this
                existing = session.query(Notification)\
                    .filter(
                        Notification.pattern_type == 'frequent_rule',
                        Notification.title.like(f'Frequent usage of {rule_name}%'),
                        Notification.creation_time >= start_date
                    )\
                    .first()
                    
                if existing:
                    continue  # Skip if already notified
                    
                # Create notification if requested
                if create_notification and config.get('notification', 'enabled'):
                    notification = Notification(
                        title=f'Frequent usage of {rule_name} ({count} times)',
                        message=f'The rule "{rule_name}" has been executed {count} times in the last {window_hours} hours.',
                        pattern_type='frequent_rule',
                        priority=2 if count >= threshold * 2 else 1,
                        confidence=0.9
                    )
                    session.add(notification)
                
                frequent_rules.append({
                    'rule_id': rule_id,
                    'rule_name': rule_name,
                    'execution_count': count,
                    'time_window_hours': window_hours
                })
            
            # Commit if we created notifications
            if create_notification and frequent_rules:
                db_manager.commit_session(session)
                
            return frequent_rules
            
        finally:
            db_manager.close_session(session)
    
    @staticmethod
    def detect_frequent_component_usage(threshold=None, window_hours=None, create_notification=True):
        """Detect components that are used frequently within a time window."""
        # Get configuration
        threshold = threshold or config.get('notification', 'threshold')
        window_hours = window_hours or config.get('notification', 'window_hours')
        
        session = db_manager.get_session()
        try:
            # Set time range
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=window_hours)
            
            # Query for components used more than threshold times in the window
            results = session.query(
                Component.id,
                Component.component_name,
                Rule.rule_name,
                func.count(ComponentExecution.id).label('execution_count')
            )\
            .join(Rule, Component.rule_id == Rule.id)\
            .join(ComponentExecution, Component.id == ComponentExecution.component_id)\
            .join(RuleExecution, ComponentExecution.rule_execution_id == RuleExecution.id)\
            .filter(ComponentExecution.execution_time >= start_date)\
            .group_by(Component.id)\
            .having(func.count(ComponentExecution.id) >= threshold)\
            .all()
            
            frequent_components = []
            for comp_id, comp_name, rule_name, count in results:
                # Check if we already have a notification for this
                existing = session.query(Notification)\
                    .filter(
                        Notification.pattern_type == 'frequent_component',
                        Notification.title.like(f'Frequent usage of {comp_name}%'),
                        Notification.creation_time >= start_date
                    )\
                    .first()
                    
                if existing:
                    continue  # Skip if already notified
                    
                # Create notification if requested
                if create_notification and config.get('notification', 'enabled'):
                    notification = Notification(
                        title=f'Frequent usage of {comp_name} ({count} times)',
                        message=f'The component "{comp_name}" from rule "{rule_name}" '
                                f'has been executed {count} times in the last {window_hours} hours.',
                        pattern_type='frequent_component',
                        priority=2 if count >= threshold * 2 else 1,
                        confidence=0.9
                    )
                    session.add(notification)
                
                frequent_components.append({
                    'component_id': comp_id,
                    'component_name': comp_name,
                    'rule_name': rule_name,
                    'execution_count': count,
                    'time_window_hours': window_hours
                })
            
            # Commit if we created notifications
            if create_notification and frequent_components:
                db_manager.commit_session(session)
                
            return frequent_components
            
        finally:
            db_manager.close_session(session)
    
    @staticmethod
    def detect_rule_component_co_occurrence(threshold=None, window_hours=None, create_notification=True):
        """Detect patterns where multiple components from different rules are used together."""
        # Get configuration
        threshold = threshold or max(2, config.get('notification', 'threshold') - 1)
        window_hours = window_hours or config.get('notification', 'window_hours')
        
        session = db_manager.get_session()
        try:
            # Set time range
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=window_hours)
            
            # This is a complex pattern detection that would normally require 
            # multiple queries and analytics. For simplicity, we'll focus on
            # finding rules that are used together in the same context window.
            
            # First, get all context windows in the timeframe
            context_windows = session.query(ContextWindow.id)\
                .filter(
                    ContextWindow.start_time >= start_date,
                    ContextWindow.rule_executions.any()
                )\
                .all()
                
            # Skip if no context windows
            if not context_windows:
                return []
                
            # Convert to list of IDs
            context_window_ids = [cw.id for cw in context_windows]
            
            # Count rule occurrences per context window to find co-occurrences
            co_occurrences = []
            
            # This is a simplified approach - in a real implementation,
            # we'd use a more sophisticated algorithm to detect patterns
            for i, cw_id in enumerate(context_window_ids):
                # Get all rules used in this context window
                rules = session.query(Rule.id, Rule.rule_name)\
                    .join(RuleExecution, Rule.id == RuleExecution.rule_id)\
                    .filter(RuleExecution.context_window_id == cw_id)\
                    .distinct()\
                    .all()
                    
                # Need at least 2 rules for co-occurrence
                if len(rules) < 2:
                    continue
                    
                # Create pairs of rules that co-occur
                for j, rule1 in enumerate(rules):
                    for rule2 in rules[j+1:]:
                        # Check if this pair occurs frequently
                        pair_key = f"{rule1.rule_name}+{rule2.rule_name}"
                        
                        # In a real implementation, we'd track these pairs more efficiently
                        co_occurrences.append(pair_key)
            
            # Count occurrences of each pair
            pairs_count = {}
            for pair in co_occurrences:
                pairs_count[pair] = pairs_count.get(pair, 0) + 1
                
            # Filter for pairs that occur >= threshold times
            frequent_pairs = []
            for pair, count in pairs_count.items():
                if count >= threshold:
                    rule1, rule2 = pair.split('+')
                    
                    # Check if we already have a notification for this
                    existing = session.query(Notification)\
                        .filter(
                            Notification.pattern_type == 'rule_co_occurrence',
                            Notification.title.like(f'Co-occurrence of {rule1} and {rule2}%'),
                            Notification.creation_time >= start_date
                        )\
                        .first()
                        
                    if existing:
                        continue  # Skip if already notified
                        
                    # Create notification if requested
                    if create_notification and config.get('notification', 'enabled'):
                        notification = Notification(
                            title=f'Co-occurrence of {rule1} and {rule2} ({count} times)',
                            message=f'The rules "{rule1}" and "{rule2}" are frequently used together '
                                    f'({count} times in the last {window_hours} hours).',
                            pattern_type='rule_co_occurrence',
                            priority=1,
                            confidence=0.8
                        )
                        session.add(notification)
                    
                    frequent_pairs.append({
                        'rule1': rule1,
                        'rule2': rule2,
                        'co_occurrence_count': count,
                        'time_window_hours': window_hours
                    })
            
            # Commit if we created notifications
            if create_notification and frequent_pairs:
                db_manager.commit_session(session)
                
            return frequent_pairs
            
        finally:
            db_manager.close_session(session)
    
    @staticmethod
    def detect_all_patterns():
        """Run all pattern detection algorithms and return results."""
        patterns = {
            'frequent_rules': PatternDetector.detect_frequent_rule_usage(),
            'frequent_components': PatternDetector.detect_frequent_component_usage(),
            'rule_co_occurrences': PatternDetector.detect_rule_component_co_occurrence()
        }
        
        return patterns

# Create functions for external use
def detect_patterns():
    """Run all pattern detection algorithms and return results."""
    return PatternDetector.detect_all_patterns()

def check_unread_notifications():
    """Get all unread notifications."""
    return db_manager.get_unread_notifications()

def mark_notification_read(notification_id):
    """Mark a notification as read."""
    return db_manager.mark_notification_read(notification_id)
