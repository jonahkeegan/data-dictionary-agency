#!/usr/bin/env python3
"""
Metrics calculation module for .clinerules analytics.
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc

from ..db.manager import db_manager
from ..db.schema import (
    ContextWindow, Rule, Component, 
    RuleExecution, ComponentExecution, Notification
)

class MetricsCalculator:
    """Calculates metrics and insights from rule execution data."""
    
    @staticmethod
    def get_context_window_metrics(context_window_id=None, session_id=None):
        """Get metrics for a specific context window."""
        session = db_manager.get_session()
        try:
            # Find the context window
            if context_window_id:
                context_window = session.query(ContextWindow).filter_by(id=context_window_id).first()
            elif session_id:
                context_window = session.query(ContextWindow).filter_by(session_id=session_id).first()
            else:
                return None
                
            if not context_window:
                return None
                
            # Count unique rules triggered
            rule_count = session.query(func.count(func.distinct(RuleExecution.rule_id)))\
                .filter(RuleExecution.context_window_id == context_window.id)\
                .scalar() or 0
                
            # Get all rule executions for this context window
            rule_executions = session.query(RuleExecution)\
                .filter(RuleExecution.context_window_id == context_window.id)\
                .all()
                
            # Build list of rules with details
            rules_triggered = []
            component_count = 0
            
            for rule_exec in rule_executions:
                # Get rule details
                rule = session.query(Rule).filter_by(id=rule_exec.rule_id).first()
                if not rule:
                    continue
                    
                # Count components triggered
                comp_execs = session.query(ComponentExecution)\
                    .filter(ComponentExecution.rule_execution_id == rule_exec.id)\
                    .all()
                    
                component_count += len(comp_execs)
                
                # Get component details
                components = []
                for comp_exec in comp_execs:
                    component = session.query(Component).filter_by(id=comp_exec.component_id).first()
                    if component:
                        components.append({
                            'name': component.component_name,
                            'execution_time': comp_exec.execution_time.isoformat(),
                            'id': component.id
                        })
                
                # Add rule to the list
                rules_triggered.append({
                    'rule_name': rule.rule_name,
                    'execution_time': rule_exec.execution_time.isoformat(),
                    'components': components,
                    'task_document': rule_exec.task_document
                })
            
            # Calculate session duration
            duration = None
            if context_window.end_time:
                duration = (context_window.end_time - context_window.start_time).total_seconds()
            
            # Build result
            result = {
                'context_window_id': context_window.id,
                'session_id': context_window.session_id,
                'start_time': context_window.start_time.isoformat(),
                'end_time': context_window.end_time.isoformat() if context_window.end_time else None,
                'status': context_window.status,
                'token_count': context_window.token_count,
                'duration_seconds': duration,
                'rule_count': rule_count,
                'component_count': component_count,
                'rules_triggered': rules_triggered
            }
            
            return result
            
        finally:
            db_manager.close_session(session)
    
    @staticmethod
    def get_rule_usage_metrics(rule_name=None, days=30):
        """Get usage metrics for a specific rule or all rules."""
        session = db_manager.get_session()
        try:
            # Set time range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Base query
            query = session.query(
                Rule.rule_name,
                func.count(RuleExecution.id).label('execution_count'),
                func.count(func.distinct(RuleExecution.context_window_id)).label('context_window_count')
            )\
            .join(RuleExecution, Rule.id == RuleExecution.rule_id)\
            .filter(RuleExecution.execution_time >= start_date)\
            .group_by(Rule.id)
            
            # Filter by rule name if provided
            if rule_name:
                query = query.filter(Rule.rule_name == rule_name)
                
            # Execute query
            results = query.all()
            
            # Format results
            rule_metrics = []
            for result in results:
                rule_name, exec_count, context_count = result
                
                # Get rule ID
                rule = session.query(Rule).filter_by(rule_name=rule_name).first()
                if not rule:
                    continue
                    
                # Get component metrics for this rule
                component_metrics = session.query(
                    Component.component_name,
                    func.count(ComponentExecution.id).label('execution_count')
                )\
                .join(ComponentExecution, Component.id == ComponentExecution.component_id)\
                .join(RuleExecution, ComponentExecution.rule_execution_id == RuleExecution.id)\
                .filter(
                    Component.rule_id == rule.id,
                    RuleExecution.execution_time >= start_date
                )\
                .group_by(Component.id)\
                .all()
                
                components = []
                for comp_name, comp_count in component_metrics:
                    components.append({
                        'name': comp_name,
                        'execution_count': comp_count
                    })
                
                rule_metrics.append({
                    'rule_name': rule_name,
                    'execution_count': exec_count,
                    'context_window_count': context_count,
                    'components': components
                })
            
            # Create summary
            summary = {
                'total_rules': len(rule_metrics),
                'total_executions': sum(r['execution_count'] for r in rule_metrics),
                'total_context_windows': sum(r['context_window_count'] for r in rule_metrics),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                }
            }
            
            return {
                'summary': summary,
                'rules': rule_metrics
            }
            
        finally:
            db_manager.close_session(session)
    
    @staticmethod
    def get_component_usage_metrics(component_name=None, rule_name=None, days=30):
        """Get usage metrics for components."""
        session = db_manager.get_session()
        try:
            # Set time range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Base query
            query = session.query(
                Component.component_name,
                Rule.rule_name,
                func.count(ComponentExecution.id).label('execution_count')
            )\
            .join(Rule, Component.rule_id == Rule.id)\
            .join(ComponentExecution, Component.id == ComponentExecution.component_id)\
            .join(RuleExecution, ComponentExecution.rule_execution_id == RuleExecution.id)\
            .filter(ComponentExecution.execution_time >= start_date)\
            .group_by(Component.id)
            
            # Apply filters
            if component_name:
                query = query.filter(Component.component_name == component_name)
                
            if rule_name:
                query = query.filter(Rule.rule_name == rule_name)
                
            # Execute query
            results = query.all()
            
            # Format results
            component_metrics = []
            for result in results:
                comp_name, rule_name, exec_count = result
                
                component_metrics.append({
                    'component_name': comp_name,
                    'rule_name': rule_name,
                    'execution_count': exec_count
                })
            
            # Create summary
            summary = {
                'total_components': len(component_metrics),
                'total_executions': sum(c['execution_count'] for c in component_metrics),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                }
            }
            
            return {
                'summary': summary,
                'components': component_metrics
            }
            
        finally:
            db_manager.close_session(session)
    
    @staticmethod
    def get_session_metrics(days=30, limit=100):
        """Get metrics for recent context window sessions."""
        session = db_manager.get_session()
        try:
            # Set time range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query recent sessions
            context_windows = session.query(ContextWindow)\
                .filter(ContextWindow.start_time >= start_date)\
                .order_by(desc(ContextWindow.start_time))\
                .limit(limit)\
                .all()
                
            # Calculate metrics for each session
            session_metrics = []
            for context_window in context_windows:
                # Count rules and components
                rule_count = session.query(func.count(func.distinct(RuleExecution.rule_id)))\
                    .filter(RuleExecution.context_window_id == context_window.id)\
                    .scalar() or 0
                    
                component_count = session.query(func.count(ComponentExecution.id))\
                    .join(RuleExecution, ComponentExecution.rule_execution_id == RuleExecution.id)\
                    .filter(RuleExecution.context_window_id == context_window.id)\
                    .scalar() or 0
                
                # Calculate duration
                duration = None
                if context_window.end_time:
                    duration = (context_window.end_time - context_window.start_time).total_seconds()
                
                session_metrics.append({
                    'session_id': context_window.session_id,
                    'context_window_id': context_window.id,
                    'start_time': context_window.start_time.isoformat(),
                    'end_time': context_window.end_time.isoformat() if context_window.end_time else None,
                    'status': context_window.status,
                    'token_count': context_window.token_count,
                    'duration_seconds': duration,
                    'rule_count': rule_count,
                    'component_count': component_count
                })
            
            # Create summary
            summary = {
                'total_sessions': len(session_metrics),
                'average_rules_per_session': sum(s['rule_count'] for s in session_metrics) / len(session_metrics) if session_metrics else 0,
                'average_components_per_session': sum(s['component_count'] for s in session_metrics) / len(session_metrics) if session_metrics else 0,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                }
            }
            
            return {
                'summary': summary,
                'sessions': session_metrics
            }
            
        finally:
            db_manager.close_session(session)
    
    @staticmethod
    def export_metrics_to_json(output_file=None, days=30):
        """Export comprehensive metrics to a JSON file."""
        try:
            # Gather all metrics
            all_metrics = {
                'rule_usage': MetricsCalculator.get_rule_usage_metrics(days=days),
                'component_usage': MetricsCalculator.get_component_usage_metrics(days=days),
                'sessions': MetricsCalculator.get_session_metrics(days=days),
                'generated_at': datetime.now().isoformat(),
                'timespan_days': days
            }
            
            # Write to file if specified
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(all_metrics, f, indent=2)
                print(f"Metrics exported to {output_file}")
                
            return all_metrics
            
        except Exception as e:
            print(f"Error exporting metrics: {e}")
            return None
