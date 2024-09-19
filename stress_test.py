import argparse
import csv
import requests
import time
from threading import Thread, Lock
import queue
from loguru import logger
import os
import random
import yaml
import sys
import signal


class StressTest:
    """
    The class is testing population mock
    """

    def __init__(self, domains, num_threads, total_requests, timeout, output_csv, log_level):
        self.domains = domains
        self.num_threads = num_threads
        self.total_requests_made = total_requests
        self.timeout = timeout
        self.output_csv = output_csv
        self.headers = {'Authorization': 'Token I_am_under_stress_when_I_test'}
        self.total_errors = 0
        self.response_times = []
        self.lock = Lock()

        logger.info("Initializing StressTest instance.")
        self.setup_logging(log_level)
        self.setup_directories()
        self.setup_csv()  # Initialize CSV with headers
        self.request_queue = queue.Queue()
        self.domain_array = []

        logger.info(f"StressTest initialized with {num_threads} threads and {total_requests} total requests.")

    def setup_logging(self, log_level):
        """
        Init logging
        @param log_level: INFO,WARNING,ERROR,DEBUG
        """
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        log_filename = f'{log_dir}/stress_test_{time.strftime("%Y%m%d_%H%M%S")}.log'
        logger.remove()
        logger.add(log_filename, level=log_level, format="{time} - {level} - {message}", rotation="1 day",
                   retention="7 days")
        logger.info('File logging setup complete.')
        logger.add(sys.stdout, level=log_level, format="{time} - {level} - {message}")
        logger.info('Console logging setup complete.')

    def setup_directories(self):
        """
        Create results directory for CSV

        """
        logger.info("Setting up directories for results and logs.")
        results_dir = 'results'
        os.makedirs(results_dir, exist_ok=True)
        self.output_csv = f'{results_dir}/results_{time.strftime("%Y%m%d_%H%M%S")}.csv'

    def setup_csv(self):
        """
        Initialize the CSV file with headers.

        """
        logger.info(f"Setting up CSV file at {self.output_csv}")
        with open(self.output_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Iteration', 'Domain', 'Response Time (s)', 'Status', 'Response JSON'])

    def worker(self, iteration):
        """
        The function sending the requests to the selected domains using the defined API URL
        @param iteration: the parameter propagated from user arguments as number of requests

        """
        logger.info(f"Worker {iteration} starting.")
        while not self.request_queue.empty():
            domain = self.request_queue.get()
            if domain not in self.domain_array:
                self.domain_array.append(domain)
            url = f"https://microcks.gin.dev.securingsam.io/rest/Reputation+API/1.0.0/domain/ranking/{domain}"
            try:
                logger.info(f"Iteration {iteration}: Querying domain: {domain}")
                start_time = time.time()
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                end_time = time.time()
                response_time = end_time - start_time
                status = response.status_code

                if status == 200:
                    response_json = response.json()  # Get JSON response
                    with self.lock:
                        self.response_times.append(response_time)
                    logger.info(f"Iteration {iteration}: Successfully queried {domain} (Status 200)")
                    logger.debug(f"Response JSON for {domain}: {response_json}")

                else:
                    with self.lock:
                        self.total_errors += 1
                    logger.error(f"Iteration {iteration}: Request to {url} failed with status code {status}")

            except requests.RequestException as e:
                with self.lock:
                    self.total_errors += 1
                logger.error(f"Iteration {iteration}: Request to {url} failed with exception: {e}")

            finally:
                self.request_queue.task_done()
                logger.info(f"Worker {iteration} completed processing {domain}")

    def stress_test(self):
        """
        Randomly choosing the domain and sending requests
        """
        try:
            for counter in range(self.total_requests_made):
                random_domain = random.choice(self.domains)  # Select a random domain for each request
                self.request_queue.put(random_domain)

            start_time = time.time()

            threads = []

            for i in range(self.num_threads):
                logger.info(f"Starting thread {i + 1}.")
                thread = Thread(target=self.worker, args=(i + 1,))  # Pass iteration number
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join(self.timeout)
                if thread.is_alive():
                    logger.warning("Timeout reached. Stopping the test.")
                    break

            end_time = time.time()
            self.calculate_statistics(end_time - start_time)

        except KeyboardInterrupt:
            logger.debug("Keyboard interrupt detected. Stopping stress test.")
            self.is_running = False  # Stop the workers
            # Wait for the threads to finish their current work
            for thread in threads:
                thread.join()
            logger.info("Test stopped by user.")
            sys.exit(0)

    def calculate_statistics(self, total_time):
        """
        Calculation of requests statistics
        @param total_time: end time minus start time
        """
        logger.info("Calculating statistics.")
        average_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        max_time = max(self.response_times) if self.response_times else 0
        p90_time = sorted(self.response_times)[
            int(0.9 * len(self.response_times))] if self.response_times else 0
        error_rate = (self.total_errors / self.total_requests_made) * 100
        logger.info(f"Writing summary results to {self.output_csv}")

        with open(self.output_csv, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([])
            writer.writerow(['Summary'])
            writer.writerow(['Total domains tested', len(self.domain_array)])
            writer.writerow(["All domains that were used", self.domain_array])
            writer.writerow(['Total Requests Made', self.total_requests_made])
            writer.writerow(['Total Errors', self.total_errors])
            writer.writerow(["Error percentage", "{:.2f}%".format(error_rate)])
            writer.writerow(['Average Response Time (s)', f"{average_time:.6f}"])
            writer.writerow(['Max Response Time (s)', f"{max_time:.6f}"])
            writer.writerow(['90th Percentile Response Time (s)', f"{p90_time:.6f}"])
            writer.writerow(['Total Test Time (s)', f"{total_time:.2f}"])
            writer.writerow(['~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'])

        logger.info(
            f"Test completed\nTotal Time: {total_time:.2f} seconds\nTotal Requests: {self.total_requests_made}\n"
            f"Error Rate: {error_rate:.2f}%\nAverage Time: {average_time:.6f} seconds\n"
            f"Max Time: {max_time:.6f} seconds\n90th Percentile Time: {p90_time:.6f} seconds")


def fetch_domains_from_yaml(file_path):
    """
    fetch domains from predefined YAML file
    @param file_path: path to the file
    """
    logger.info(f"Loading domains from YAML file: {file_path}")
    with open(file_path, 'r') as file:
        domains_data = yaml.safe_load(file)
    domains = domains_data.get('domains', [])
    logger.info(f"Loaded {len(domains)} domains from YAML file.")
    return domains


def parse_arguments():
    """
    Arguments coming from the user command line
    """
    logger.info("Parsing command-line arguments.")
    parser = argparse.ArgumentParser(description='Stress test for Reputation service.')
    parser.add_argument('--yaml-file', type=str, required=True, help='Path to YAML file containing domains')
    parser.add_argument('--threads', type=int, default=10, help='Number of concurrent threads')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout in seconds')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Logging level')
    parser.add_argument('--total-requests', type=int, default=100, help='Total number of random requests to make')
    return parser.parse_args()


def main():
    """
    Main function initiate a class
    """
    args = parse_arguments()
    domains = fetch_domains_from_yaml(args.yaml_file)
    stress_test = StressTest(domains, args.threads, args.total_requests, args.timeout, '', args.log_level)
    stress_test.stress_test()


if __name__ == "__main__":
    main()
