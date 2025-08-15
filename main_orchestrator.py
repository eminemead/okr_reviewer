#!/usr/bin/env python3
"""
OKR Pipeline Orchestrator

This script orchestrates the entire OKR processing pipeline:
1. Generate OKR reports from Feishu API
2. Extract metrics from reports into DuckDB
3. Export data to CSV files
4. Generate insights and analysis
5. Start the FastHTML dashboard

Usage:
    python main_orchestrator.py [--okr_limit N] [--skip-dashboard] [--port PORT]
"""

import os
import sys
import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path

class OKRPipelineOrchestrator:
    def __init__(self, okr_limit=2, skip_dashboard=False, port=8000):
        self.okr_limit = okr_limit
        self.skip_dashboard = skip_dashboard
        self.port = port
        self.start_time = datetime.now()
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp and level."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_script(self, script_name, description, args=None):
        """Run a Python script and handle errors."""
        self.log(f"Starting: {description}")
        
        cmd = ["uv", "run", "python", script_name]
        if args:
            cmd.extend(args)
            
        self.log(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                cwd=os.getcwd()
            )
            
            if result.stdout:
                self.log(f"Output from {script_name}:")
                print(result.stdout)
                
            self.log(f"Completed: {description}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Error running {script_name}: {e}", "ERROR")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
            
    def check_prerequisites(self):
        """Check if required environment variables and files exist."""
        self.log("Checking prerequisites...")
        
        # Check for access token
        if not os.getenv("FEISHU_ACCESS_TOKEN"):
            self.log("Warning: FEISHU_ACCESS_TOKEN not set", "WARNING")
            self.log("You may need to set it before running: export FEISHU_ACCESS_TOKEN='your_token'", "WARNING")
        
        # Check for required scripts
        required_scripts = [
            "generate_okr_report.py",
            "extract_okr_metrics.py", 
            "export_metrics.py",
            "summary_insights.py",
            "fasthtml_dashboard.py"
        ]
        
        missing_scripts = []
        for script in required_scripts:
            if not Path(script).exists():
                missing_scripts.append(script)
                
        if missing_scripts:
            self.log(f"Missing required scripts: {missing_scripts}", "ERROR")
            return False
            
        self.log("Prerequisites check completed")
        return True
        
    def step1_generate_reports(self):
        """Step 1: Generate OKR reports from Feishu API."""
        self.log("=" * 60)
        self.log("STEP 1: Generating OKR Reports")
        self.log("=" * 60)
        
        args = ["--okr_limit", str(self.okr_limit)]
        return self.run_script(
            "generate_okr_report.py",
            "OKR Report Generation",
            args
        )
        
    def step2_extract_metrics(self):
        """Step 2: Extract metrics from OKR reports into DuckDB."""
        self.log("=" * 60)
        self.log("STEP 2: Extracting Metrics")
        self.log("=" * 60)
        
        # Find the most recent OKR report
        reports_dir = Path("outputs/reports")
        if not reports_dir.exists():
            self.log("No reports directory found. Skipping metrics extraction.", "WARNING")
            return False
            
        report_files = list(reports_dir.glob("okr_report_*.md"))
        if not report_files:
            self.log("No OKR report files found. Skipping metrics extraction.", "WARNING")
            return False
            
        # Get the most recent report
        latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
        self.log(f"Using latest report: {latest_report}")
        
        # Update the extract script to use the latest report
        return self.run_script(
            "extract_okr_metrics.py",
            "Metrics Extraction",
            [str(latest_report)]
        )
        
    def step3_export_data(self):
        """Step 3: Export metrics data to CSV files."""
        self.log("=" * 60)
        self.log("STEP 3: Exporting Data")
        self.log("=" * 60)
        
        return self.run_script(
            "export_metrics.py",
            "Data Export"
        )
        
    def step4_generate_insights(self):
        """Step 4: Generate insights and analysis."""
        self.log("=" * 60)
        self.log("STEP 4: Generating Insights")
        self.log("=" * 60)
        
        return self.run_script(
            "summary_insights.py",
            "Insights Generation"
        )
        
    def step5_start_dashboard(self):
        """Step 5: Start the FastHTML dashboard."""
        if self.skip_dashboard:
            self.log("Dashboard startup skipped (--skip-dashboard flag)")
            return True
            
        self.log("=" * 60)
        self.log("STEP 5: Starting Dashboard")
        self.log("=" * 60)
        
        # Update dashboard port if needed
        dashboard_script = Path("fasthtml_dashboard.py")
        if dashboard_script.exists():
            # Read current content
            with open(dashboard_script, 'r') as f:
                content = f.read()
            
            # Update port if different from default
            if self.port != 8000:
                # Replace the serve call with new port
                import re
                content = re.sub(
                    r'serve\(host="0\.0\.0\.0", port=\d+\)',
                    f'serve(host="0.0.0.0", port={self.port})',
                    content
                )
                
                with open(dashboard_script, 'w') as f:
                    f.write(content)
                    
                self.log(f"Updated dashboard port to {self.port}")
        
        # Start dashboard in background
        cmd = ["uv", "run", "python", "fasthtml_dashboard.py"]
        self.log(f"Starting dashboard: {' '.join(cmd)}")
        
        try:
            # Start in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for startup
            time.sleep(3)
            
            if process.poll() is None:
                self.log(f"Dashboard started successfully on port {self.port}")
                self.log(f"Access at: http://127.0.0.1:{self.port}")
                return True
            else:
                stdout, stderr = process.communicate()
                self.log(f"Dashboard failed to start", "ERROR")
                if stdout: print("STDOUT:", stdout)
                if stderr: print("STDERR:", stderr)
                return False
                
        except Exception as e:
            self.log(f"Error starting dashboard: {e}", "ERROR")
            return False
            
    def run_pipeline(self):
        """Run the complete OKR pipeline."""
        self.log("Starting OKR Pipeline Orchestrator")
        self.log(f"Configuration: OKR Limit={self.okr_limit}, Skip Dashboard={self.skip_dashboard}, Port={self.port}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.log("Prerequisites check failed. Exiting.", "ERROR")
            return False
            
        # Run pipeline steps
        steps = [
            ("Generate Reports", self.step1_generate_reports),
            ("Extract Metrics", self.step2_extract_metrics),
            ("Export Data", self.step3_export_data),
            ("Generate Insights", self.step4_generate_insights),
            ("Start Dashboard", self.step5_start_dashboard)
        ]
        
        success_count = 0
        for step_name, step_func in steps:
            if step_func():
                success_count += 1
            else:
                self.log(f"Step '{step_name}' failed", "ERROR")
                # Continue with next steps even if one fails
                
        # Summary
        total_time = datetime.now() - self.start_time
        self.log("=" * 60)
        self.log("PIPELINE COMPLETED")
        self.log("=" * 60)
        self.log(f"Steps completed: {success_count}/{len(steps)}")
        self.log(f"Total time: {total_time}")
        
        if success_count == len(steps):
            self.log("All steps completed successfully! 🎉", "SUCCESS")
        else:
            self.log(f"{len(steps) - success_count} steps failed", "WARNING")
            
        return success_count == len(steps)

def main():
    parser = argparse.ArgumentParser(
        description="OKR Pipeline Orchestrator - Run the complete OKR processing pipeline"
    )
    parser.add_argument(
        "--okr_limit", 
        type=int, 
        default=2,
        help="Number of OKRs to fetch per user (default: 2)"
    )
    parser.add_argument(
        "--skip-dashboard", 
        action="store_true",
        help="Skip starting the dashboard (run all other steps)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port for the dashboard (default: 8000)"
    )
    
    args = parser.parse_args()
    
    orchestrator = OKRPipelineOrchestrator(
        okr_limit=args.okr_limit,
        skip_dashboard=args.skip_dashboard,
        port=args.port
    )
    
    success = orchestrator.run_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

