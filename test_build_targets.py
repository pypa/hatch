import argparse

# Simulate the argument parser behavior
parser = argparse.ArgumentParser()
parser.add_argument('-t', '--target', dest='targets', action='append', help='Comma-separated list of targets')

# Test case 1: Multiple -t flags
args1 = parser.parse_args(['-t', 'wheel', '-t', 'sdist'])
print(f"Test 1 (multiple -t flags): {args1.targets}")

# Test case 2: Comma-separated targets
args2 = parser.parse_args(['-t', 'wheel,sdist'])
print(f"Test 2 (comma-separated): {args2.targets}")
