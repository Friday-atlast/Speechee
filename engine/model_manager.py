"""
Speechee - Model Manager
Download, verify, and manage Whisper models.
"""

import os
import sys
import requests
from pathlib import Path

# Import config from same package
try:
    from .config import EngineConfig  # When imported as module
except ImportError:
    from config import EngineConfig   # When run directly


class ModelManager:
    """Manage Whisper model downloads and verification."""
    
    def __init__(self):
        self.config = EngineConfig
        self._ensure_models_dir()
    
    def _ensure_models_dir(self):
        """Create models directory if not exists."""
        self.config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _print_progress(self, downloaded: int, total: int, width: int = 40):
        """Print download progress bar."""
        if total <= 0:
            return
        
        percent = (downloaded / total) * 100
        filled = int(width * downloaded / total)
        bar = "█" * filled + "░" * (width - filled)
        mb_done = downloaded / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        
        sys.stdout.write(f"\r  [{bar}] {percent:5.1f}% ({mb_done:.1f}/{mb_total:.1f} MB)")
        sys.stdout.flush()
    
    def download_model(self, model_name: str, force: bool = False) -> bool:
        """
        Download a specific model.
        
        Args:
            model_name: Model name (tiny.en, tiny, base, small)
            force: Re-download even if exists
            
        Returns:
            True if successful
        """
        # Validate model name
        try:
            info = self.config.get_model_info(model_name)
        except ValueError as e:
            print(f"[ERROR] {e}")
            return False
        
        dest_path = Path(info["path"])
        
        # Check existing file
        if dest_path.exists() and not force:
            file_size_mb = dest_path.stat().st_size / (1024 * 1024)
            expected_size = info["size_mb"]
            
            # Allow 5% tolerance for size check
            if abs(file_size_mb - expected_size) < expected_size * 0.05:
                print(f"[SKIP] {model_name} already exists ({file_size_mb:.1f} MB)")
                return True
            else:
                print(f"[WARN] {model_name} size mismatch ({file_size_mb:.1f} MB vs {expected_size} MB expected)")
                print(f"       Re-downloading...")
        
        # Download
        url = info["url"]
        print(f"\n[DOWNLOAD] {model_name}")
        print(f"  URL:      {url}")
        print(f"  Size:     ~{info['size_mb']} MB")
        print(f"  Language: {info['language']}")
        print(f"  Dest:     {dest_path}")
        print()
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self._print_progress(downloaded, total_size)
            
            print(f"\n[SUCCESS] {model_name} downloaded!")
            return True
            
        except requests.exceptions.Timeout:
            print(f"\n[ERROR] Download timeout. Check internet connection.")
            self._cleanup_partial(dest_path)
            return False
            
        except requests.exceptions.ConnectionError:
            print(f"\n[ERROR] Connection failed. Check internet connection.")
            self._cleanup_partial(dest_path)
            return False
            
        except requests.exceptions.HTTPError as e:
            print(f"\n[ERROR] HTTP Error: {e}")
            self._cleanup_partial(dest_path)
            return False
            
        except KeyboardInterrupt:
            print(f"\n[CANCELLED] Download stopped by user.")
            self._cleanup_partial(dest_path)
            return False
            
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            self._cleanup_partial(dest_path)
            return False
    
    def _cleanup_partial(self, path: Path):
        """Remove partially downloaded file."""
        if path.exists():
            try:
                path.unlink()
                print(f"  Cleaned up partial file.")
            except Exception:
                pass
    
    def download_all(self, force: bool = False) -> dict:
        """
        Download all 4 models.
        
        Returns:
            Dict with model names and success status
        """
        models = ["tiny.en", "tiny", "base", "small"]
        results = {}
        
        print("=" * 65)
        print("DOWNLOADING ALL MODELS")
        print("=" * 65)
        
        for i, model in enumerate(models, 1):
            print(f"\n[{i}/{len(models)}] Processing {model}...")
            results[model] = self.download_model(model, force)
        
        return results
    
    def download_essential(self, force: bool = False) -> dict:
        """
        Download essential models for low-end devices.
        Models: tiny.en (English) + tiny (Multilingual)
        
        Returns:
            Dict with results
        """
        models = ["tiny.en", "tiny"]
        results = {}
        
        print("=" * 65)
        print("DOWNLOADING ESSENTIAL MODELS")
        print("(Optimized for low-end devices: i3, 4GB RAM)")
        print("=" * 65)
        
        for i, model in enumerate(models, 1):
            print(f"\n[{i}/{len(models)}] Processing {model}...")
            results[model] = self.download_model(model, force)
        
        return results
    
    def download_recommended(self, force: bool = False) -> dict:
        """
        Download recommended models.
        Models: tiny.en + tiny + base
        
        Returns:
            Dict with results
        """
        models = ["tiny.en", "tiny", "base"]
        results = {}
        
        print("=" * 65)
        print("DOWNLOADING RECOMMENDED MODELS")
        print("(For balanced speed and accuracy)")
        print("=" * 65)
        
        for i, model in enumerate(models, 1):
            print(f"\n[{i}/{len(models)}] Processing {model}...")
            results[model] = self.download_model(model, force)
        
        return results
    
    def verify_model(self, model_name: str) -> dict:
        """
        Verify model file integrity.
        
        Returns:
            Dict with verification details
        """
        try:
            info = self.config.get_model_info(model_name)
        except ValueError as e:
            return {"valid": False, "error": str(e)}
        
        path = Path(info["path"])
        
        if not path.exists():
            return {
                "valid": False,
                "model": model_name,
                "error": "File not found",
                "expected_path": str(path)
            }
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        expected_size = info["size_mb"]
        size_ok = abs(file_size_mb - expected_size) < expected_size * 0.05
        
        return {
            "valid": size_ok,
            "model": model_name,
            "path": str(path),
            "actual_size_mb": round(file_size_mb, 2),
            "expected_size_mb": expected_size,
            "size_match": size_ok,
            "language": info["language"],
            "ram_required_mb": info["ram_mb"]
        }
    
    def verify_all(self) -> dict:
        """Verify all models."""
        results = {}
        for model in self.config.list_all_models():
            results[model] = self.verify_model(model)
        return results
    
    def list_models(self, verbose: bool = False):
        """Print formatted list of models."""
        print("\n" + "=" * 70)
        print("SPEECHEE - MODEL STATUS")
        print("=" * 70)
        
        print(f"\n{'Model':<10} {'Size':<8} {'RAM':<8} {'Language':<15} {'Speed':<10} {'Status':<12}")
        print("-" * 70)
        
        for model_name in self.config.list_all_models():
            info = self.config.get_model_info(model_name)
            status = "✓ Ready" if info["exists"] else "✗ Missing"
            
            print(f"{model_name:<10} {info['size_mb']:<8} {info['ram_mb']:<8} {info['language']:<15} {info['speed']:<10} {status:<12}")
            
            if verbose and info["exists"]:
                print(f"           Path: {info['path']}")
        
        print("-" * 70)
        
        downloaded = self.config.list_downloaded_models()
        total = len(self.config.MODELS)
        
        print(f"\nSummary: {len(downloaded)}/{total} models downloaded")
        
        if downloaded:
            print(f"Ready:   {', '.join(downloaded)}")
        
        missing = set(self.config.list_all_models()) - set(downloaded)
        if missing:
            print(f"Missing: {', '.join(missing)}")
        
        print("=" * 70)
    
    def get_best_model(self, max_ram_mb: int = 500, multilingual: bool = False) -> str:
        """
        Get best available model within constraints.
        
        Args:
            max_ram_mb: Maximum RAM usage
            multilingual: Require multilingual support
            
        Returns:
            Model name or None
        """
        downloaded = self.config.list_downloaded_models()
        
        if not downloaded:
            return None
        
        # Priority order (most accurate first)
        if multilingual:
            priority = ["small", "base", "tiny"]
        else:
            priority = ["small", "base", "tiny.en", "tiny"]
        
        for model in priority:
            if model in downloaded:
                info = self.config.get_model_info(model)
                if info["ram_mb"] <= max_ram_mb:
                    if multilingual and info["language"] != "multilingual":
                        continue
                    return model
        
        # Fallback to any available
        return downloaded[0]
    
    def get_total_size(self) -> dict:
        """Get total size of downloaded models."""
        total_mb = 0
        count = 0
        
        for model in self.config.list_downloaded_models():
            path = self.config.get_model_path(model)
            if path.exists():
                total_mb += path.stat().st_size / (1024 * 1024)
                count += 1
        
        return {
            "total_mb": round(total_mb, 2),
            "total_gb": round(total_mb / 1024, 2),
            "model_count": count
        }


# ================================================================
# CLI INTERFACE
# ================================================================

def print_help():
    """Print detailed help message."""
    help_text = """
================================================================================
SPEECHEE MODEL MANAGER - HELP
================================================================================

USAGE:
  python model_manager.py <command> [options]

COMMANDS:
  list                    List all models with status
  download --model NAME   Download specific model
  verify --model NAME     Verify model integrity
  essential               Download tiny.en + tiny (low-end devices)
  recommended             Download tiny.en + tiny + base
  all                     Download all 4 models
  help                    Show this help message

OPTIONS:
  --model, -m NAME        Model name (tiny.en, tiny, base, small)
  --force, -f             Force re-download even if exists
  --verbose, -v           Show detailed output

EXAMPLES:
  # List all models
  python model_manager.py list
  
  # Download specific model
  python model_manager.py download --model tiny
  
  # Download essential models (tiny.en + tiny)
  python model_manager.py essential
  
  # Download recommended models (tiny.en + tiny + base)
  python model_manager.py recommended
  
  # Download all models
  python model_manager.py all
  
  # Verify specific model
  python model_manager.py verify --model base
  
  # Force re-download
  python model_manager.py download --model tiny --force

MODELS:
  tiny.en     75 MB    English only, fastest
  tiny        75 MB    Multilingual, fastest (Hindi/Hinglish)
  base       142 MB    Multilingual, balanced
  small      466 MB    Multilingual, better accuracy

================================================================================
"""
    print(help_text)


def main():
    """Command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speechee Model Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # Custom help handling
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        choices=["list", "download", "verify", "essential", "recommended", "all", "help"],
        help="Command to execute"
    )
    parser.add_argument(
        "--model", "-m",
        help="Model name (tiny.en, tiny, base, small)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-download"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--help", "-h",
        action="store_true",
        help="Show help message"
    )
    
    args = parser.parse_args()
    
    # Handle help
    if args.help or args.command == "help":
        print_help()
        return
    
    manager = ModelManager()
    
    # Execute command
    if args.command == "list":
        manager.list_models(verbose=args.verbose)
    
    elif args.command == "download":
        if not args.model:
            print("[ERROR] Specify model with --model")
            print(f"Available: {EngineConfig.list_all_models()}")
            sys.exit(1)
        success = manager.download_model(args.model, force=args.force)
        sys.exit(0 if success else 1)
    
    elif args.command == "verify":
        if args.model:
            result = manager.verify_model(args.model)
            print(f"\n[VERIFY] {args.model}")
            print("-" * 40)
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            results = manager.verify_all()
            print("\n[VERIFY ALL MODELS]")
            print("-" * 40)
            for model, result in results.items():
                status = "✓ Valid" if result.get("valid") else "✗ Invalid"
                print(f"  {model}: {status}")
    
    elif args.command == "essential":
        manager.download_essential(force=args.force)
        print("\n")
        manager.list_models()
    
    elif args.command == "recommended":
        manager.download_recommended(force=args.force)
        print("\n")
        manager.list_models()
    
    elif args.command == "all":
        manager.download_all(force=args.force)
        print("\n")
        manager.list_models()
        
        # Show total size
        size_info = manager.get_total_size()
        print(f"\nTotal disk usage: {size_info['total_mb']:.0f} MB ({size_info['total_gb']:.2f} GB)")
    
    elif args.command is None:
        # No command - show interactive menu
        print("\n" + "=" * 65)
        print("SPEECHEE MODEL MANAGER")
        print("=" * 65)
        print("\nNo command specified. Options:\n")
        print("  1. python model_manager.py list          - List all models")
        print("  2. python model_manager.py essential     - Download tiny.en + tiny")
        print("  3. python model_manager.py recommended   - Download tiny.en + tiny + base")
        print("  4. python model_manager.py all           - Download all 4 models")
        print("  5. python model_manager.py download -m <name>  - Download specific model")
        print("  6. python model_manager.py help          - Show detailed help")
        print("\nRunning 'recommended' download...\n")
        
        manager.download_recommended()
        print("\n")
        manager.list_models()
    
    else:
        print_help()


if __name__ == "__main__":
    main()