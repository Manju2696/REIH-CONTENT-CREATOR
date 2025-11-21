"""
Database setup for workflow automation pipeline
Uses MongoDB for flexible document storage
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId
from datetime import datetime
from typing import Optional, List, Dict, Any
import os
import json
import re
import hashlib

# MongoDB connection settings
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://Manjunath:*GbMVdGUfL_M22q@cluster0.skwiezx.mongodb.net/?appName=Cluster0')
DB_NAME = os.getenv('MONGO_DB_NAME', 'REih_content_creator')

# Global client and database instances
_client = None
_db = None

def get_db_connection():
    """Get MongoDB database connection"""
    global _client, _db
    if _client is None:
        try:
            _client = MongoClient(MONGO_URI)
            _db = _client[DB_NAME]
            # Test connection
            _client.admin.command('ping')
        except ConnectionFailure:
            raise ConnectionError("Failed to connect to MongoDB")
    return _db

def init_db():
    """Initialize database with all required collections and indexes"""
    db = get_db_connection()
    
    # Collections are created automatically on first insert
    # We'll create indexes for better performance
    
    # Workflows collection
    db.workflows.create_index("is_active")
    db.workflows.create_index("name")
    
    # Pipeline stages collection
    db.pipeline_stages.create_index("workflow_id")
    db.pipeline_stages.create_index([("workflow_id", 1), ("stage_order", 1)])
    
    # Workflow instances collection
    db.workflow_instances.create_index("workflow_id")
    db.workflow_instances.create_index("status")
    db.workflow_instances.create_index("created_at")
    
    # Task executions collection
    db.task_executions.create_index("workflow_instance_id")
    db.task_executions.create_index("status")
    db.task_executions.create_index("pipeline_stage_id")
    
    # Automation rules collection
    db.automation_rules.create_index("workflow_id")
    db.automation_rules.create_index("is_active")
    
    # Data records collection
    db.data_records.create_index("record_type")
    db.data_records.create_index("workflow_instance_id")
    db.data_records.create_index([("record_type", 1), ("record_key", 1)], unique=True)
    
    # Workflow logs collection
    db.workflow_logs.create_index("workflow_instance_id")
    db.workflow_logs.create_index("task_execution_id")
    db.workflow_logs.create_index("created_at")
    
    # Users collection
    db.users.create_index("email", unique=True)
    db.users.create_index("is_active")
    
    # Blog URLs collection
    db.blog_urls.create_index("status")
    db.blog_urls.create_index("url", unique=True)
    db.blog_urls.create_index("created_at")
    
    # Scripts collection
    db.scripts.create_index("blog_url_id")
    db.scripts.create_index("status")
    db.scripts.create_index([("blog_url_id", 1), ("script_number", 1)])
    db.scripts.create_index("created_at")
    
    # Videos collection
    db.videos.create_index("script_id")
    db.videos.create_index("status")
    db.videos.create_index("created_at")
    
    # Social media posts collection
    db.social_media_posts.create_index("video_id")
    db.social_media_posts.create_index("platform")
    db.social_media_posts.create_index([("video_id", 1), ("platform", 1)], unique=True)
    
    # Uploaded videos collection (for upload video page)
    db.uploaded_videos.create_index("created_at")
    db.uploaded_videos.create_index("title")
    
    # Reimaginehome TV uploads collection
    db.reimaginehome_tv_uploads.create_index("video_id")
    db.reimaginehome_tv_uploads.create_index("status")
    
    # YouTube upload tracking collection
    db.youtube_upload_tracking.create_index("upload_date", unique=True)
    
    # Master prompts collection
    db.master_prompts.create_index("is_active")
    db.master_prompts.create_index("name")
    
    print("Database initialized successfully!")

def _get_consistent_id_hash(object_id) -> int:
    """Get consistent hash from ObjectId using MD5 (consistent across Python sessions)"""
    if isinstance(object_id, ObjectId):
        obj_str = str(object_id)
    else:
        obj_str = str(object_id)
    # Use MD5 for consistent hashing (same input always gives same output)
    hash_obj = hashlib.md5(obj_str.encode())
    # Convert first 8 bytes to integer (consistent)
    hash_int = int(hash_obj.hexdigest()[:8], 16)
    return hash_int % (10**9)

def _find_objectid_by_hash(collection, hash_value: int) -> Optional[ObjectId]:
    """Find ObjectId from hash value by searching all documents in collection"""
    try:
        hash_int = int(hash_value)
        for doc in collection.find({}):
            doc_id = doc.get('_id')
            if doc_id:
                doc_hash = _get_consistent_id_hash(doc_id)
                if doc_hash == hash_int:
                    return doc_id
    except Exception as e:
        print(f"Error finding ObjectId by hash: {e}")
    return None

def _parse_sql_where(where_clause: str, params: tuple, collection_name: str = None) -> Dict[str, Any]:
    """Parse SQL WHERE clause to MongoDB filter"""
    if not where_clause:
        return {}
    
    filter_dict = {}
    param_index = 0
    
    # Find all ? placeholders and their corresponding operators
    # Pattern to match: field operator ?
    pattern = r'(\w+)\s*(=|!=|>|<|>=|<=)\s*\?'
    matches = list(re.finditer(pattern, where_clause, re.IGNORECASE))
    
    for match in matches:
        field = match.group(1)
        operator = match.group(2).strip()
        
        if param_index < len(params):
            value = params[param_index]
            
            # Map SQL operators to MongoDB operators
            if operator == '=':
                if field == 'id':
                    # Handle id field - convert hash to ObjectId if needed
                    if isinstance(value, str) and len(value) == 24:
                        try:
                            # Try to parse as ObjectId string
                            filter_dict['_id'] = ObjectId(value)
                        except:
                            # Not a valid ObjectId, treat as hash
                            if collection_name:
                                db = get_db_connection()
                                collection = db[collection_name]
                                obj_id = _find_objectid_by_hash(collection, int(value))
                                if obj_id:
                                    filter_dict['_id'] = obj_id
                                else:
                                    filter_dict['_id'] = value
                            else:
                                filter_dict['_id'] = value
                    elif isinstance(value, (int, str)):
                        # It's likely a hash value - find the ObjectId
                        try:
                            hash_int = int(value)
                            if collection_name:
                                db = get_db_connection()
                                collection = db[collection_name]
                                # Try to find ObjectId by hash
                                obj_id = _find_objectid_by_hash(collection, hash_int)
                                if obj_id:
                                    filter_dict['_id'] = obj_id
                                else:
                                    # If not found, store hash to try again in execute_update/delete
                                    # This handles edge cases where collection_name might not be available
                                    filter_dict['_id_hash'] = hash_int
                                    filter_dict['_collection_name'] = collection_name
                            else:
                                # No collection name, store hash for later lookup
                                filter_dict['_id_hash'] = hash_int
                        except Exception as e:
                            # If conversion fails, treat as direct value
                            filter_dict['_id'] = value
                    else:
                        filter_dict['_id'] = value
                else:
                    filter_dict[field] = value
            elif operator == '!=':
                if field == 'id':
                    filter_dict['_id'] = {'$ne': value}
                else:
                    filter_dict[field] = {'$ne': value}
            elif operator == '>':
                filter_dict[field] = {'$gt': value}
            elif operator == '<':
                filter_dict[field] = {'$lt': value}
            elif operator == '>=':
                filter_dict[field] = {'$gte': value}
            elif operator == '<=':
                filter_dict[field] = {'$lte': value}
            
            param_index += 1
    
    return filter_dict

def _convert_row_to_dict(row: Dict) -> Dict:
    """Convert MongoDB document to dict, handling ObjectId and other types"""
    result = {}
    for key, value in row.items():
        if key == '_id':
            # Convert ObjectId to int for backward compatibility using consistent hash
            if isinstance(value, ObjectId):
                # Use consistent hash of ObjectId to generate a consistent int ID
                result['id'] = _get_consistent_id_hash(value)
                # Also store the ObjectId string for lookups (hidden field)
                result['_object_id'] = str(value)
            else:
                result['id'] = value
                result['_object_id'] = str(value) if value else None
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            # Keep datetime as string for JSON compatibility
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return results as list of dictionaries"""
    db = get_db_connection()
    
    # Parse SQL query
    query = query.strip()
    
    # Check if this is a COUNT query (supports COUNT(*) and COUNT(DISTINCT ...))
    count_match = re.search(r'SELECT\s+COUNT\s*\(\s*(?:\*|DISTINCT\s+\w+)\s*\)\s+as\s+(\w+)', query, re.IGNORECASE)
    if count_match:
        # Handle COUNT(*) and COUNT(DISTINCT ...) queries
        count_alias = count_match.group(1)
        
        # Extract table name
        table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        if not table_match:
            raise ValueError(f"Could not parse table name from COUNT query: {query}")
        
        collection_name = table_match.group(1)
        collection = db[collection_name]
        
        # Parse WHERE clause
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
        filter_dict = {}
        if where_match:
            where_clause = where_match.group(1).strip()
            filter_dict = _parse_sql_where(where_clause, params, collection_name)
        
        # Use MongoDB's count_documents for COUNT queries
        count = collection.count_documents(filter_dict)
        return [{count_alias: count}]
    
    # Regular SELECT query
    # Extract table name
    table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
    if not table_match:
        raise ValueError(f"Could not parse table name from query: {query}")
    
    collection_name = table_match.group(1)
    collection = db[collection_name]
    
    # Parse WHERE clause
    where_match = re.search(r'WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
    filter_dict = {}
    if where_match:
        where_clause = where_match.group(1).strip()
        filter_dict = _parse_sql_where(where_clause, params, collection_name)
    
    # Parse ORDER BY - support multiple fields and table aliases (e.g., "bu.updated_at DESC, bu.created_at DESC")
    order_by_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
    sort_list = []
    if order_by_match:
        order_by_clause = order_by_match.group(1).strip()
        # Split by comma to handle multiple fields
        order_fields = [f.strip() for f in order_by_clause.split(',')]
        for order_field in order_fields:
            # Match field name (may include table alias like "bu.updated_at") and direction
            field_match = re.search(r'(\w+\.\w+|\w+)(?:\s+(ASC|DESC))?', order_field, re.IGNORECASE)
            if field_match:
                field_full = field_match.group(1)
                direction = field_match.group(2)
                # Remove table alias if present (e.g., "bu.updated_at" -> "updated_at")
                if '.' in field_full:
                    field = field_full.split('.')[-1]
                else:
                    field = field_full
                sort_direction = -1 if direction and direction.upper() == 'DESC' else 1
                sort_list.append((field, sort_direction))
    
    # Parse LIMIT
    limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
    limit = None
    if limit_match:
        limit = int(limit_match.group(1))
    
    # Execute query
    cursor = collection.find(filter_dict)
    if sort_list:
        cursor = cursor.sort(sort_list)
    if limit:
        cursor = cursor.limit(limit)
    
    results = []
    for doc in cursor:
        results.append(_convert_row_to_dict(doc))
    
    return results

def execute_update(query: str, params: tuple = ()) -> int:
    """Execute UPDATE/DELETE query and return affected rows"""
    db = get_db_connection()
    
    # Store original query for parsing (don't uppercase yet - it breaks regex)
    original_query = query.strip()
    query_upper = original_query.upper()
    
    if query_upper.startswith('UPDATE'):
        # Parse UPDATE query (use original for regex matching)
        table_match = re.search(r'UPDATE\s+(\w+)', original_query, re.IGNORECASE)
        if not table_match:
            raise ValueError(f"Could not parse table name from UPDATE query: {original_query}")
        
        collection_name = table_match.group(1)
        collection = db[collection_name]
        
        # Parse SET clause (use original query)
        set_match = re.search(r'SET\s+(.+?)(?:\s+WHERE|$)', original_query, re.IGNORECASE | re.DOTALL)
        if not set_match:
            raise ValueError(f"Could not parse SET clause from UPDATE query: {original_query}")
        
        set_clause = set_match.group(1).strip()
        update_dict = {}
        
        # Parse SET assignments like "field = ?" or "field = CURRENT_TIMESTAMP" or "field = 0"
        # Handle parameterized values and literal values
        param_index = 0
        assignments = [part.strip() for part in set_clause.split(',')]
        
        def _parse_literal(value_str):
            value_str = value_str.strip()
            if value_str.startswith("'") and value_str.endswith("'"):
                return value_str[1:-1]
            if value_str.startswith('"') and value_str.endswith('"'):
                return value_str[1:-1]
            # Try to parse as int/float
            try:
                if '.' in value_str:
                    return float(value_str)
                return int(value_str)
            except ValueError:
                pass
            # Booleans
            if value_str.lower() in ['true', 'false']:
                return value_str.lower() == 'true'
            if value_str.lower() == 'null':
                return None
            return value_str
        
        for assignment in assignments:
            if not assignment:
                continue
            match = re.match(r'(\w+)\s*=\s*(.+)$', assignment)
            if not match:
                continue
            field = match.group(1)
            value_expr = match.group(2).strip()
            
            if value_expr.upper() == 'CURRENT_TIMESTAMP':
                update_dict[field] = datetime.now()
            elif value_expr == '?':
                if param_index < len(params):
                    value = params[param_index]
                    param_index += 1
                else:
                    value = None
                if field.endswith('_at') and isinstance(value, str):
                    try:
                        if value.upper() == 'CURRENT_TIMESTAMP':
                            update_dict[field] = datetime.now()
                        else:
                            update_dict[field] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        update_dict[field] = datetime.now()
                else:
                    update_dict[field] = value
            else:
                update_dict[field] = _parse_literal(value_expr)
        
        # Parse WHERE clause (use original query)
        where_match = re.search(r'WHERE\s+(.+?)$', original_query, re.IGNORECASE | re.DOTALL)
        filter_dict = {}
        if where_match:
            where_clause = where_match.group(1).strip()
            # Adjust params for WHERE clause (skip SET params)
            where_params = params[param_index:] if param_index < len(params) else ()
            filter_dict = _parse_sql_where(where_clause, where_params, collection_name)
        
        # Handle _id_hash case (when id is a hash value)
        # First try to find ObjectId using hash lookup
        if '_id_hash' in filter_dict:
            hash_value = filter_dict.pop('_id_hash')
            collection_name_for_lookup = filter_dict.pop('_collection_name', collection_name)
            
            # Try to find ObjectId by hash
            obj_id = _find_objectid_by_hash(collection, hash_value)
            if obj_id:
                filter_dict['_id'] = obj_id
            else:
                # Hash lookup failed - try querying the database directly to get ObjectId
                # This handles cases where hash doesn't match (e.g., old data with different hash)
                try:
                    # Query all documents and check their hash
                    for doc in collection.find({}):
                        doc_id = doc.get('_id')
                        if doc_id:
                            doc_hash = _get_consistent_id_hash(doc_id)
                            if doc_hash == hash_value:
                                filter_dict['_id'] = doc_id
                                break
                    # If still not found, return 0
                    if '_id' not in filter_dict:
                        print(f"Warning: Could not find document with hash {hash_value} in {collection_name}")
                        return 0
                except Exception as e:
                    print(f"Error looking up document by hash: {e}")
                    return 0
        
        # Execute update
        if filter_dict and '_id' in filter_dict:
            # Update specific document(s) by _id
            result = collection.update_many(filter_dict, {"$set": update_dict})
            return result.modified_count
        elif not filter_dict:
            # No WHERE clause - update all documents
            result = collection.update_many({}, {"$set": update_dict})
            return result.modified_count
        else:
            # WHERE clause exists but no _id - try to update matching documents
            result = collection.update_many(filter_dict, {"$set": update_dict})
            return result.modified_count
    
    elif query_upper.startswith('DELETE'):
        # Parse DELETE query (use original for regex matching)
        table_match = re.search(r'DELETE\s+FROM\s+(\w+)', original_query, re.IGNORECASE)
        if not table_match:
            raise ValueError(f"Could not parse table name from DELETE query: {original_query}")
        
        collection_name = table_match.group(1)
        collection = db[collection_name]
        
        # Parse WHERE clause (use original query)
        where_match = re.search(r'WHERE\s+(.+?)$', original_query, re.IGNORECASE | re.DOTALL)
        filter_dict = {}
        if where_match:
            where_clause = where_match.group(1).strip()
            filter_dict = _parse_sql_where(where_clause, params, collection_name)
        
        # Handle _id_hash case (when id is a hash value)
        # First try to find ObjectId using hash lookup
        if '_id_hash' in filter_dict:
            hash_value = filter_dict.pop('_id_hash')
            collection_name_for_lookup = filter_dict.pop('_collection_name', collection_name)
            
            # Try to find ObjectId by hash
            obj_id = _find_objectid_by_hash(collection, hash_value)
            if obj_id:
                filter_dict['_id'] = obj_id
            else:
                # Hash lookup failed - try querying the database directly to get ObjectId
                try:
                    # Query all documents and check their hash
                    for doc in collection.find({}):
                        doc_id = doc.get('_id')
                        if doc_id:
                            doc_hash = _get_consistent_id_hash(doc_id)
                            if doc_hash == hash_value:
                                filter_dict['_id'] = doc_id
                                break
                    # If still not found, return 0
                    if '_id' not in filter_dict:
                        print(f"Warning: Could not find document with hash {hash_value} in {collection_name}")
                        return 0
                except Exception as e:
                    print(f"Error looking up document by hash: {e}")
                    return 0
        
        # Also delete related data (cascade delete)
        # Delete scripts, videos, and related data first
        if collection_name == 'blog_urls' and '_id' in filter_dict:
            blog_object_id = filter_dict.get('_id')
            scripts_collection = db['scripts']
            
            # Find all scripts for this blog (blog_url_id might be stored as hash or ObjectId)
            # Query all scripts and find those that match
            scripts_to_delete = []
            for script in scripts_collection.find({}):
                script_blog_id = script.get('blog_url_id')
                if script_blog_id:
                    # Check if it matches the blog ObjectId
                    if script_blog_id == blog_object_id:
                        scripts_to_delete.append(script.get('_id'))
                    # Also check if it's a hash match
                    elif isinstance(script_blog_id, (int, str)):
                        try:
                            script_hash = int(script_blog_id)
                            blog_hash = _get_consistent_id_hash(blog_object_id)
                            if script_hash == blog_hash:
                                scripts_to_delete.append(script.get('_id'))
                        except:
                            pass
            
            # Delete scripts and their related data
            videos_collection = db['videos']
            social_posts_collection = db['social_media_posts']
            
            for script_id in scripts_to_delete:
                # Find all videos for this script (script_id might be stored as ObjectId or hash)
                videos_to_delete = []
                for video in videos_collection.find({}):
                    video_script_id = video.get('script_id')
                    if video_script_id:
                        # Check if it matches the script ObjectId
                        if video_script_id == script_id:
                            videos_to_delete.append(video.get('_id'))
                        # Also check if it's a hash match
                        elif isinstance(video_script_id, (int, str)):
                            try:
                                video_script_hash = int(video_script_id)
                                script_hash = _get_consistent_id_hash(script_id)
                                if video_script_hash == script_hash:
                                    videos_to_delete.append(video.get('_id'))
                            except:
                                pass
                
                # Delete social media posts for these videos
                for video_id in videos_to_delete:
                    social_posts_collection.delete_many({'video_id': video_id})
                
                # Delete videos
                for video_id in videos_to_delete:
                    videos_collection.delete_one({'_id': video_id})
                
                # Delete the script
                scripts_collection.delete_one({'_id': script_id})
        
        # Execute delete
        if not filter_dict:
            print("Warning: Empty filter_dict in execute_delete - no documents will be deleted")
            return 0
        
        if '_id' not in filter_dict:
            print(f"Warning: No '_id' in filter_dict for delete operation. Filter: {filter_dict}")
            return 0
        
        try:
            result = collection.delete_many(filter_dict)
            deleted_count = result.deleted_count
            if deleted_count == 0:
                print(f"Warning: Delete operation found 0 documents to delete. Filter: {filter_dict}")
            return deleted_count
        except Exception as e:
            print(f"Error executing delete: {e}")
            print(f"Filter dict: {filter_dict}")
            raise
    
    else:
        raise ValueError(f"Unsupported query type: {query}")

def execute_insert(query: str, params: tuple = ()) -> int:
    """Execute INSERT query and return last inserted row id"""
    db = get_db_connection()
    
    # Parse INSERT query
    query = query.strip()
    
    # Extract table name
    table_match = re.search(r'INSERT\s+INTO\s+(\w+)', query, re.IGNORECASE)
    if not table_match:
        raise ValueError(f"Could not parse table name from INSERT query: {query}")
    
    collection_name = table_match.group(1)
    collection = db[collection_name]
    
    # Parse column names
    columns_match = re.search(r'\(([^)]+)\)', query)
    if not columns_match:
        raise ValueError(f"Could not parse columns from INSERT query: {query}")
    
    columns = [col.strip() for col in columns_match.group(1).split(',')]
    
    # Build document
    doc = {}
    for i, col in enumerate(columns):
        if i < len(params):
            value = params[i]
            # Handle special cases
            if col == 'id':
                if value is None:
                    continue  # Skip id, MongoDB will generate _id
                else:
                    # Store id as _id for MongoDB
                    doc['_id'] = value
                    continue
            if col.endswith('_at') and value is None:
                value = datetime.now()
            elif col.endswith('_at') and isinstance(value, str):
                # Try to parse datetime string
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    value = datetime.now()
            doc[col] = value
    
    # Add timestamps if not provided
    if 'created_at' not in doc:
        doc['created_at'] = datetime.now()
    if 'updated_at' not in doc:
        doc['updated_at'] = datetime.now()
    
    # Insert document
    result = collection.insert_one(doc)
    
    # Return a numeric ID for backward compatibility using consistent hash
    inserted_id = result.inserted_id
    if isinstance(inserted_id, ObjectId):
        # Convert ObjectId to int using consistent hash
        return _get_consistent_id_hash(inserted_id)
    return int(inserted_id) if isinstance(inserted_id, int) else _get_consistent_id_hash(inserted_id)
