#!/usr/bin/env python3
"""
Database schema for .clinerules logger using SQLAlchemy.
Enhanced with automatic system interaction tracking.
"""

import datetime
import json
from sqlalchemy import (
    create_engine, Column, Integer, String, 
    DateTime, Text, ForeignKey, Boolean, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class ContextWindow(Base):
    """Represents a Cline AI context window session."""
    
    __tablename__ = 'context_windows'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.datetime.now)
    end_time = Column(DateTime, nullable=True)
    token_count = Column(Integer, default=0)
    status = Column(String(20), default='active')
    
    # Relationships
    rule_executions = relationship('RuleExecution', back_populates='context_window')
    
    def __repr__(self):
        return f"<ContextWindow(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"


class Rule(Base):
    """Represents a .clinerules file."""
    
    __tablename__ = 'rules'
    
    id = Column(Integer, primary_key=True)
    rule_name = Column(String(100), nullable=False, index=True)
    file_path = Column(String(255), nullable=True)
    first_seen = Column(DateTime, default=datetime.datetime.now)
    description = Column(Text, nullable=True)
    execution_count = Column(Integer, default=0)
    
    # Relationships
    components = relationship('Component', back_populates='rule')
    executions = relationship('RuleExecution', back_populates='rule')
    
    def __repr__(self):
        return f"<Rule(id={self.id}, rule_name='{self.rule_name}')>"


class Component(Base):
    """Represents a component or section within a .clinerules file."""
    
    __tablename__ = 'components'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False)
    component_name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    execution_count = Column(Integer, default=0)
    
    # Relationships
    rule = relationship('Rule', back_populates='components')
    executions = relationship('ComponentExecution', back_populates='component')
    
    def __repr__(self):
        return f"<Component(id={self.id}, component_name='{self.component_name}')>"


class RuleExecution(Base):
    """Represents a .clinerules rule execution event."""
    
    __tablename__ = 'rule_executions'
    
    id = Column(Integer, primary_key=True)
    context_window_id = Column(Integer, ForeignKey('context_windows.id'))
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False)
    execution_time = Column(DateTime, default=datetime.datetime.now)
    task_document = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    context_window = relationship('ContextWindow', back_populates='rule_executions')
    rule = relationship('Rule', back_populates='executions')
    component_executions = relationship('ComponentExecution', back_populates='rule_execution')
    
    def __repr__(self):
        return f"<RuleExecution(id={self.id}, execution_time='{self.execution_time}')>"


class ComponentExecution(Base):
    """Represents a .clinerules component execution event."""
    
    __tablename__ = 'component_executions'
    
    id = Column(Integer, primary_key=True)
    rule_execution_id = Column(Integer, ForeignKey('rule_executions.id'), nullable=False)
    component_id = Column(Integer, ForeignKey('components.id'), nullable=False)
    execution_time = Column(DateTime, default=datetime.datetime.now)
    notes = Column(Text, nullable=True)
    
    # Relationships
    rule_execution = relationship('RuleExecution', back_populates='component_executions')
    component = relationship('Component', back_populates='executions')
    
    def __repr__(self):
        return f"<ComponentExecution(id={self.id}, execution_time='{self.execution_time}')>"


class Notification(Base):
    """Represents a notification generated based on pattern detection."""
    
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    pattern_type = Column(String(50), nullable=False)
    creation_time = Column(DateTime, default=datetime.datetime.now)
    read = Column(Boolean, default=False)
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    confidence = Column(Float, default=1.0)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}', read={self.read})>"


class FileInteraction(Base):
    """Represents a .clinerules file interaction event."""
    
    __tablename__ = 'file_interactions'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False)
    context_window_id = Column(Integer, ForeignKey('context_windows.id'), nullable=True)
    interaction_time = Column(DateTime, default=datetime.datetime.now)
    interaction_type = Column(String(50), nullable=False)  # 'read', 'write', 'validate', 'execute'
    application = Column(String(100))  # 'vscode', 'cli', etc.
    user_initiated = Column(Boolean, default=False)
    meta_data = Column(Text)  # JSON metadata about interaction
    
    # Relationships
    rule = relationship('Rule')
    context_window = relationship('ContextWindow')
    
    def __repr__(self):
        return f"<FileInteraction(id={self.id}, rule_name='{self.rule.rule_name if self.rule else None}', type='{self.interaction_type}')>"
    
    def set_metadata(self, metadata_dict):
        """Set metadata as JSON string."""
        if metadata_dict is not None:
            self.meta_data = json.dumps(metadata_dict)
    
    def get_metadata(self):
        """Get metadata as Python dictionary."""
        if self.meta_data:
            try:
                return json.loads(self.meta_data)
            except json.JSONDecodeError:
                return {}
        return {}


class SystemEvent(Base):
    """Represents a system event related to .clinerules."""
    
    __tablename__ = 'system_events'
    
    id = Column(Integer, primary_key=True)
    event_time = Column(DateTime, default=datetime.datetime.now)
    event_type = Column(String(100), nullable=False)
    source = Column(String(100))
    event_details = Column(Text)  # JSON details about the event
    
    def __repr__(self):
        return f"<SystemEvent(id={self.id}, event_type='{self.event_type}', source='{self.source}')>"
    
    def set_details(self, details_dict):
        """Set details as JSON string."""
        if details_dict is not None:
            self.event_details = json.dumps(details_dict)
    
    def get_details(self):
        """Get details as Python dictionary."""
        if self.event_details:
            try:
                return json.loads(self.event_details)
            except json.JSONDecodeError:
                return {}
        return {}


def create_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)
