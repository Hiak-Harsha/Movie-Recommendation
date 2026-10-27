import os
import zipfile
import datetime

def make_clean_zip():
    desktop_zip = r"C:\Users\madha\Desktop\CineMatch_Project.zip"
    root_dir = r"C:\Users\madha\Desktop\Movie Recommendation"
    
    exclude_dirs = {
        '.git',
        'node_modules',
        '.next',
        '__pycache__',
        '.pytest_cache',
        '.venv',
        'venv'
    }
    
    if os.path.exists(desktop_zip):
        try:
            os.remove(desktop_zip)
            print(f"Removed previous zip: {desktop_zip}")
        except Exception as e:
            print(f"Warning removing previous zip: {e}")
            
    file_count = 0
    with zipfile.ZipFile(desktop_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            for f in filenames:
                if f.endswith(('.pyc', '.pyo', '.zip')):
                    continue
                full_path = os.path.join(dirpath, f)
                arcname = os.path.relpath(full_path, root_dir)
                zipf.write(full_path, arcname)
                file_count += 1
                
    project_zip = os.path.join(root_dir, "CineMatch_Project.zip")
    import shutil
    shutil.copy2(desktop_zip, project_zip)
    
    size_mb = os.path.getsize(project_zip) / (1024 * 1024)
    print(f"Successfully created:")
    print(f"  1. Inside project folder: {project_zip}")
    print(f"  2. On Desktop:           {desktop_zip}")
    print(f"Total files: {file_count}")
    print(f"Archive size: {size_mb:.2f} MB")
    
    # Verification
    critical_files = [
        'apps/web/src/app/globals.css',
        'apps/web/src/app/page.tsx',
        'apps/web/src/app/movie/[id]/page.tsx',
        'apps/web/src/stage/Stage.tsx',
        'apps/web/src/stage/Story.tsx',
        'apps/web/src/stage/Dock.tsx',
        'apps/web/src/modules/search/Scene.tsx',
        'apps/web/src/modules/taste/Scene.tsx',
        'apps/web/src/modules/foryou/Scene.tsx',
        'apps/web/src/modules/tune/Scene.tsx',
        'apps/web/src/modules/library/Scene.tsx',
        'apps/web/src/modules/detail/DetailOverlay.tsx',
        'apps/web/src/modules/about/AboutDrawer.tsx',
        'apps/web/src/modules/about/ModelReportTab.tsx',
        'apps/api/main.py',
        'apps/api/engine.py',
        'apps/api/sessions.py',
        'eval_results.json',
        'strategy.json',
        'README.md',
        'Dockerfile.api',
        'Dockerfile.web',
        'docker-compose.yml',
    ]
    
    with zipfile.ZipFile(desktop_zip, 'r') as verify_zip:
        names = set(verify_zip.namelist())
        print("\nVerifying Critical Files:")
        all_present = True
        for cf in critical_files:
            present = cf in names
            status = "OK" if present else "MISSING"
            if not present:
                all_present = False
            print(f"  [{status}] {cf}")
            
    if all_present:
        print("\n--> ALL CRITICAL FILES PRESENT AND VERIFIED.")
    else:
        print("\n--> ERROR: SOME CRITICAL FILES ARE MISSING.")

if __name__ == "__main__":
    make_clean_zip()
