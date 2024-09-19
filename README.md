# Domain Stress Test

This script is designed to stress test multiple domains by sending concurrent HTTP requests and recording response times, statuses, and potential errors.

## Installation

To install the required dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Usage
```bash
python stress_test.py --yaml-file assets/domains.yaml --threads 10 --timeout 60 --total-requests 100 --log-level [INFO,ERROR,DEBUG]
```
### Command-line Arguments:
* --yaml-file: Path to the YAML file containing the list of domains to test.
* --threads: Number of threads to use for testing (default is 10).
* --timeout: Timeout for each request, in seconds (default is 60 seconds).
* --total-requests: Total number of requests to send during the test.
* --log-level: The logging level for the output. Valid options are INFO, ERROR, and DEBUG.

## Domain YAML Example
```yaml
domains:
  - google.com
  - vesty.ru
  - facebook.com
  - twitter.com
  - linkedin.com
  - youtube.com
  - reddit.com
  - instagram.com
  - netflix.com
  - microsoft.com
  - example.com
  - error.com
  - ///fkbjmfd  # Faulty URL example

```
### Output in CSV Example

```csv
Summary
----------------------------
Total domains tested: 13
All domains used: ['example.com', 'facebook.com', 'error.com', 'vesty.ru', 'reddit.com', 'twitter.com', '///fkbjmfd', 'instagram.com', 'google.com', 'linkedin.com', 'netflix.com', 'youtube.com', 'microsoft.com']
Total Requests Made: 100
Total Errors: 6
Error Percentage: 6.00%
Average Response Time (s): 0.381841
Max Response Time (s): 0.678263
90th Percentile Response Time (s): 0.388310
Total Test Time (s): 4.09
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```
