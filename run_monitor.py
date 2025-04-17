#!/usr/bin/env python3
import os
import sys
from daily_osmonitor import run as run_daily
from weekly_osmonitor import run as run_weekly

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_monitor.py [daily|weekly] [test|prod]")
        sys.exit(1)
    
    monitor_type = sys.argv[1].lower()
    env = sys.argv[2].lower()
    
    if env not in ['test', 'prod']:
        print("Environment must be either 'test' or 'prod'")
        sys.exit(1)
    
    if monitor_type not in ['daily', 'weekly']:
        print("Monitor type must be either 'daily' or 'weekly'")
        sys.exit(1)
    
    # Set the environment
    os.environ['ENV'] = env
    
    # Run the appropriate monitor
    if monitor_type == 'daily':
        run_daily()
    else:
        run_weekly()

if __name__ == "__main__":
    main()
