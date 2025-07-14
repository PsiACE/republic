"""
MkDocs hooks for the Republic documentation site.
"""

import os
import shutil

def on_post_build(config):
    """
    Hook that runs before the build process starts.
    
    Args:
        config: The MkDocs configuration object
    """
    # Ensure CNAME file is copied to the site directory
    cname_source = "CNAME"
    cname_dest = os.path.join(config.site_dir, "CNAME")
    
    if os.path.exists(cname_source):
        shutil.copy2(cname_source, cname_dest)
        print(f"[PASS] CNAME file copied to {cname_dest}")
    else:
        print("[WARNING] CNAME file not found in project root") 