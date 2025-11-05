"""
Version Management System for RAG ZIP Project
Handles version separation, metadata tracking, and version-aware operations
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from .config import DATA_DIR, VECTOR_DIR


@dataclass
class VersionMetadata:
    """Version metadata structure"""
    version_id: str
    version_name: str
    description: str
    upload_timestamp: str
    zip_filename: str
    file_count: int
    chunk_count: int
    file_types: List[str]
    vectorstore_path: str
    status: str = "active"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class VersionManager:
    """Manages versions and their metadata"""
    
    def __init__(self):
        self.versions_file = DATA_DIR / "versions.json"
        self.versions_dir = DATA_DIR / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        
    def generate_version_id(self, version_name: str = None) -> str:
        """Generate a unique version ID"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if version_name:
            # Clean version name for use in ID
            clean_name = "".join(c for c in version_name if c.isalnum() or c in ".-_")
            return f"{clean_name}-{timestamp}"
        else:
            return f"v{timestamp}"
    
    def create_version_metadata(
        self,
        version_name: str,
        description: str,
        zip_filename: str,
        file_count: int,
        chunk_count: int,
        file_types: List[str],
        tags: List[str] = None
    ) -> VersionMetadata:
        """Create version metadata"""
        version_id = self.generate_version_id(version_name)
        vectorstore_path = str(self.versions_dir / version_id)
        
        metadata = VersionMetadata(
            version_id=version_id,
            version_name=version_name,
            description=description,
            upload_timestamp=datetime.now().isoformat(),
            zip_filename=zip_filename,
            file_count=file_count,
            chunk_count=chunk_count,
            file_types=file_types,
            vectorstore_path=vectorstore_path,
            tags=tags or []
        )
        
        return metadata
    
    def save_version_metadata(self, metadata: VersionMetadata) -> bool:
        """Save version metadata to file"""
        try:
            versions = self.load_all_versions()
            versions[metadata.version_id] = asdict(metadata)
            
            with open(self.versions_file, 'w') as f:
                json.dump(versions, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving version metadata: {e}")
            return False
    
    def load_all_versions(self) -> Dict[str, dict]:
        """Load all version metadata"""
        try:
            if self.versions_file.exists():
                with open(self.versions_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading versions: {e}")
            return {}
    
    def get_version(self, version_id: str) -> Optional[VersionMetadata]:
        """Get specific version metadata"""
        versions = self.load_all_versions()
        if version_id in versions:
            return VersionMetadata(**versions[version_id])
        return None
    
    def list_versions(self, status: str = None) -> List[VersionMetadata]:
        """List all versions, optionally filtered by status"""
        versions = self.load_all_versions()
        version_list = []
        
        for version_data in versions.values():
            metadata = VersionMetadata(**version_data)
            if status is None or metadata.status == status:
                version_list.append(metadata)
        
        # Sort by upload timestamp (newest first)
        version_list.sort(key=lambda x: x.upload_timestamp, reverse=True)
        return version_list
    
    def update_version_status(self, version_id: str, status: str) -> bool:
        """Update version status"""
        try:
            versions = self.load_all_versions()
            if version_id in versions:
                versions[version_id]["status"] = status
                with open(self.versions_file, 'w') as f:
                    json.dump(versions, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Error updating version status: {e}")
            return False
    
    def delete_version(self, version_id: str) -> bool:
        """Delete version and its vectorstore"""
        try:
            versions = self.load_all_versions()
            if version_id in versions:
                # Remove vectorstore directory
                version_data = versions[version_id]
                vectorstore_path = Path(version_data["vectorstore_path"])
                if vectorstore_path.exists():
                    import shutil
                    shutil.rmtree(vectorstore_path)
                
                # Remove from metadata
                del versions[version_id]
                with open(self.versions_file, 'w') as f:
                    json.dump(versions, f, indent=2)
                
                return True
            return False
        except Exception as e:
            print(f"Error deleting version: {e}")
            return False
    
    def get_latest_version(self) -> Optional[VersionMetadata]:
        """Get the latest active version"""
        versions = self.list_versions(status="active")
        return versions[0] if versions else None
    
    def search_versions(self, query: str) -> List[VersionMetadata]:
        """Search versions by name, description, or tags"""
        all_versions = self.list_versions()
        query_lower = query.lower()
        
        matching_versions = []
        for version in all_versions:
            if (query_lower in version.version_name.lower() or
                query_lower in version.description.lower() or
                any(query_lower in tag.lower() for tag in version.tags)):
                matching_versions.append(version)
        
        return matching_versions


# Global version manager instance
version_manager = VersionManager()
