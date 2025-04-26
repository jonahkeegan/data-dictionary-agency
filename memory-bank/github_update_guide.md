# GitHub Update Guide for Data Dictionary Agency

## Overview

This document provides detailed instructions for managing ongoing updates to the [Data Dictionary Agency GitHub repository](https://github.com/jonahkeegan/data-dictionary-agency). It captures the workflow established during the initial code upload and provides step-by-step guidance for maintaining the repository.

## Repository Structure

- **Repository URL**: https://github.com/jonahkeegan/data-dictionary-agency
- **Primary Branch**: `main`
- **Local Configuration**: Git initialized in the project root directory

## Standard GitHub Workflow

### 1. Before Making Changes

Always sync your local repository with the remote to avoid conflicts:

```bash
# Change to the project directory if needed
cd C:\Users\jonah\Documents\Cline\the-data-dictionary-agency

# Fetch the latest changes
git fetch origin

# Pull latest changes from the main branch
git pull origin main
```

### 2. Making and Committing Changes

After making code changes:

```bash
# Check what files have changed
git status

# Stage all changes
git add .

# Or stage specific files
git add path/to/file1 path/to/file2

# Create a commit with a descriptive message
git commit -m "Brief description of changes"
```

#### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- First line should be 50 characters or less
- Begin with a capitalized action word (Add, Fix, Update, Refactor, etc.)
- Include the scope of the change if applicable (e.g., "Update XML parsing for nested elements")

### 3. Pushing Changes to GitHub

```bash
# Push changes to the main branch
git push origin main
```

### 4. Handling Common Scenarios

#### If Push Is Rejected

```bash
# Pull latest changes with rebase to keep commit history clean
git pull --rebase origin main

# Resolve any conflicts if they occur, then
git push origin main
```

#### Resolving Merge Conflicts

1. If merge conflicts occur during `pull` or `rebase`:
   ```bash
   # See which files have conflicts
   git status
   ```

2. Open conflicting files and look for conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)

3. Edit the files to resolve conflicts, removing conflict markers

4. After resolving:
   ```bash
   # Stage resolved files
   git add <resolved-files>
   
   # Continue the rebase
   git rebase --continue
   
   # Or if during a merge
   git merge --continue
   ```

#### Working with Branches

For significant features or changes, create a branch:

```bash
# Create and switch to a new branch
git checkout -b feature/new-format-detector

# Push the branch to GitHub
git push -u origin feature/new-format-detector

# When ready to merge back to main
git checkout main
git merge feature/new-format-detector
git push origin main
```

## Repository Topics

The repository should use the following topics for discoverability:
- `data-dictionary`
- `metadata`
- `schema`
- `documentation`
- `data-catalog`
- `python`
- `database`

To update topics:
1. Go to https://github.com/jonahkeegan/data-dictionary-agency
2. Click the gear icon (⚙️) near the "About" section
3. Add or update topics in the "Topics" field
4. Click "Save changes"

## Troubleshooting

### Git Authentication Issues

If you encounter authentication issues:

```bash
# Check remote URL configuration
git remote -v

# Update if needed (for HTTPS)
git remote set-url origin https://github.com/jonahkeegan/data-dictionary-agency.git
```

### Branch Name Mismatches

If local and remote branch names don't match:

```bash
# Rename local branch to match remote
git branch -m old-name main

# Set upstream tracking
git branch --set-upstream-to=origin/main main
```

### Editor Issues with Commit Messages

If Vim opens for commit messages and you're unfamiliar with it:
1. Press `i` to enter insert mode
2. Type your message
3. Press `Esc` to exit insert mode
4. Type `:wq` and press Enter to save and exit

Alternatively, configure a different editor:
```bash
git config --global core.editor "notepad"
```

## Best Practices for This Repository

1. **Regular Updates**: Commit and push changes frequently to avoid large, complex merges
2. **Targeted Commits**: Keep commits focused on specific changes rather than mixing unrelated modifications
3. **Documentation Updates**: Keep README and other documentation in sync with code changes
4. **Test Before Pushing**: Run tests locally before pushing to ensure code quality
5. **Update Dependencies**: Regularly review and update dependencies in requirements.txt
6. **Memory Bank Synchronization**: Ensure memory-bank documents are updated to reflect architectural changes
7. **Review .gitignore**: Periodically check that .gitignore is correctly excluding temporary and sensitive files

## Recent Updates Log

### April 26, 2025 - Protobuf Parser Implementation

#### Files Added/Modified:
- `src/format_detection/plugins/protobuf/__init__.py`: Protocol Buffers parser implementation
- `tests/unit/test_protobuf_parser.py`: Comprehensive test suite for Protobuf parser

#### Memory Bank Updates:
- Updated `progress.md`: Format parsers now at 80% completion (8 out of 10 parsers)
- Updated `task_002_second_sprint.md`: Marked Protobuf parser as complete
- Updated `activeContext.md`: Added Protobuf parser to completed components
- Updated `formats_index.yaml`: Added detailed Protobuf parser metadata
- Updated `codeMap_root.md`: Updated Protobuf parser status in PROJECT_STRUCTURE

#### Commit Message:
```
Add Protocol Buffers parser with comprehensive test suite

- Implement Protobuf parser with message, enum, oneof and map type support
- Extract nested message and enum structures
- Handle service and RPC method definitions
- Create test suite covering all major Protobuf features
- Process imports and dependencies
- Map Protocol Buffers types to normalized data types
- Update documentation to reflect Protobuf parser completion
```

### April 25, 2025 - SQL DDL Parser Testing Implementation

#### Files Added/Modified:
- `tests/unit/test_sql_parser.py`: Comprehensive test suite for SQL DDL parser
- `src/format_detection/plugins/sql/__init__.py`: No changes (verified parser implementation)

#### Memory Bank Updates:
- Updated `progress.md`: Format parsers now at 90% completion (8 out of 10 parsers)
- Updated `task_002_second_sprint.md`: Marked SQL DDL parser as complete
- Updated `activeContext.md`: Added SQL parser to completed components, updated component count
- Updated `formats_index.yaml`: Updated SQL parser metadata with detailed implementation info
- Updated `codeMap_root.md`: Added SQL parser to ACTIVE_MEMORY, updated task attribution

#### Commit Message:
```
Add comprehensive test suite for SQL DDL parser

- Implement test cases for SQL dialect detection (MySQL, PostgreSQL)
- Add tests for table definition extraction and relationships
- Create test cases for primary key and foreign key detection
- Verify constraint handling and type mapping
- Update documentation to reflect SQL parser completion
```

### April 25, 2025 - YAML Parser Implementation

#### Files Added/Modified:
- `src/format_detection/plugins/yaml/__init__.py`: YAML parser implementation
- `tests/unit/test_yaml_parser.py`: Comprehensive test suite for YAML parser
- `requirements.txt`: Added PyYAML dependency

#### Memory Bank Updates:
- Updated `progress.md`: Format parsers now at 85% completion
- Updated `task_002_second_sprint.md`: Marked YAML parser as complete
- Updated `activeContext.md`: Added YAML parser to completed components
- Updated `formats_index.yaml`: Added detailed YAML parser metadata
- Updated `codeMap_root.md`: Added YAML parser to ACTIVE_MEMORY
- Updated `techContext.md`: Added PyYAML dependency
- Updated `systemPatterns.md`: Added YAML parser to plugin architecture diagram

#### Commit Message:
```
Add YAML format parser with comprehensive test suite

- Implement YAML parser with schema extraction
- Add support for YAML anchors, aliases, multiline strings
- Create test suite with 17 test cases
- Add PyYAML dependency
- Update documentation
```

---

*This guide was created based on the GitHub upload workflow established on April 25, 2025.*
